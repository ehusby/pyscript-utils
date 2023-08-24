
import math
import os

import numpy as np
import pandas as pd
import rasterio as rio
import rasterio.features
from alive_progress import alive_bar

from psutils.noop import with_noop


def get_max_pixel_locations(rasterfile):
    ds = rio.open(rasterfile)
    array = ds.read(1)
    max_idx_flat = np.argmax(array, axis=None)
    max_value = array.take(max_idx_flat)
    max_idx_2d = np.unravel_index(max_idx_flat, array.shape)
    max_coords = ds.xy(*max_idx_2d)
    print("Max value = {} at raster index (row, col)=({}, {}), geographic coordinates (X, Y)=({}, {})".format(
        max_value, *max_idx_2d, *max_coords
    ))


def sjoin_stats(base_gdf, join_gdf, how='left', op='intersects',
                working_crs='base', output_crs='base',
                base_id_col=None, count_col='count', cover_col='cover_perc',
                agg_cols=None, agg_col_op=None, agg_col_fill=None, agg_col_suffix=None,
                agg_op_map=None, agg_fill_map=None, agg_col_map=None,
                in_cover_gdf=None, out_cover_gdf=False,
                out_raster_dir=None, raster_res=None,
                join_col_for_raster=None, raster_agg_op='count',
                raster_dtype=np.int16, raster_nodata=None,
                in_spatial_index=None, out_spatial_index=False,
                allow_modify_base=False, allow_modify_cover=False,
                show_progress=True):
    cover_gdf = in_cover_gdf

    if working_crs == 'base':
        working_crs = base_gdf.crs
    elif working_crs == 'join':
        working_crs = join_gdf.crs
    elif working_crs is None:
        raise RuntimeError

    if output_crs == 'base':
        output_crs = base_gdf.crs
    elif output_crs == 'join':
        output_crs = join_gdf.crs

    base_orig_crs = base_gdf.crs
    cover_orig_crs = cover_gdf.crs if cover_gdf is not None else base_orig_crs

    base_output_crs = output_crs if output_crs is not None else base_orig_crs
    cover_orig_crs = output_crs if output_crs is not None else cover_orig_crs

    if agg_op_map is None and agg_cols is not None:
        if agg_col_op is None:
            raise RuntimeError
        else:
            agg_op_map = {col: agg_col_op for col in agg_cols}

    if agg_op_map is not None:
        if agg_fill_map is None:
            agg_fill_map = {col: agg_col_fill for col, op in agg_op_map.items()}
        if agg_col_map is None:
            if agg_col_suffix is None:
                agg_col_map = {col: '{}_{}'.format(col, op) for col, op in agg_op_map.items()}
            else:
                agg_col_map = {col: '{}{}'.format(col, agg_col_suffix) for col, op in agg_op_map.items()}

    if in_cover_gdf is not None:
        cover_gdf = in_cover_gdf
        if cover_col not in cover_gdf.columns:
            raise RuntimeError
    else:
        cover_gdf = None

    if out_raster_dir is not None and raster_res is None:
        raise RuntimeError

    if raster_agg_op not in ('count', 'min', 'max', 'sum', 'average'):
        raise RuntimeError

    if base_gdf.crs != working_crs:
        print("Reprojecting base GDF to working CRS")
        base_gdf = base_gdf.to_crs(working_crs)
        allow_modify_base = True

    if join_gdf.crs != working_crs:
        print("Reprojecting join GDF to working CRS")
        join_gdf = join_gdf.to_crs(working_crs)

    if cover_gdf is not None and cover_gdf.crs != working_crs:
        print("Reprojecting cover GDF to working CRS")
        cover_gdf = cover_gdf.to_crs(working_crs)
        allow_modify_cover = True

    if not allow_modify_base:
        base_gdf = base_gdf.copy(deep=True)

    if in_spatial_index is not None:
        spatial_index = in_spatial_index
    else:
        print("Building spatial index")
        spatial_index = join_gdf.sindex.query_bulk(
            base_gdf.geometry, predicate=op, sort=False
        )
    si_base, si_join = spatial_index

    base_match_idx = None
    base_match_total = None
    if how == 'inner' or count_col is not None or show_progress:
        base_match_idx, base_idx_freq = np.unique(si_base, return_counts=True)
        base_match_total = len(base_match_idx)
        if count_col is not None:
            print("Adding count field")
            base_gdf[count_col] = 0
            base_gdf[count_col].values[base_match_idx] = base_idx_freq

    if out_raster_dir is not None:
        if base_id_col is not None:
            def get_raster_basename(base_gdf, base_idx):
                return str(base_gdf[base_id_col].values[base_idx])
        elif base_match_total is not None:
            base_idx_strfmt = '{:0>' + str(len(str(base_match_total))) + '}'
            def get_raster_basename(base_gdf, base_idx):
                return base_idx_strfmt.format(base_idx)
        else:
            def get_raster_basename(base_gdf, base_idx):
                return str(base_idx)

    if agg_op_map is None and cover_col is None and out_raster_dir is None:
        pass
    else:
        if agg_op_map is not None:
            print("Adding aggregate fields")
            agg_new_cols = list(agg_col_map.values())
            agg_new_cols_fill = [fill for col, fill in agg_fill_map.items()]
            base_gdf[agg_new_cols] = pd.DataFrame([agg_new_cols_fill], index=base_gdf.index)

        if cover_col is not None:
            print("Adding percent coverage field")
            if out_cover_gdf:
                if cover_gdf is None:
                    cover_gdf = base_gdf.copy(deep=True)
                    allow_modify_cover = True
                if not allow_modify_cover:
                    cover_gdf = cover_gdf.copy(deep=True)
                    allow_modify_cover = True
                if cover_col not in cover_gdf.columns:
                    cover_gdf[cover_col] = float(0)
            base_gdf[cover_col] = float(0)

        if out_raster_dir is not None:
            if not os.path.isdir(out_raster_dir):
                print("Creating output raster directory: {}".format(out_raster_dir))
                os.makedirs(out_raster_dir)

        alive_bar_func = alive_bar if show_progress else with_noop

        start_pos = 0
        curr_base_idx = si_base[start_pos]
        si_base_pos_end = len(si_base) - 1
        with alive_bar_func(base_match_total, force_tty=True) as bar:
            for pos, base_idx in enumerate(si_base):
                if base_idx != curr_base_idx:
                    end_pos = pos
                elif pos == si_base_pos_end:
                    end_pos = pos + 1
                else:
                    continue

                join_feats = join_gdf.iloc[si_join[start_pos:end_pos]]

                if agg_op_map is not None:
                    join_agg = join_feats.agg(agg_op_map)
                    for old_col, new_col in agg_col_map.items():
                        base_gdf[new_col].values[curr_base_idx] = join_agg[old_col]

                if cover_col is not None or out_raster_dir is not None:
                    base_geom = base_gdf['geometry'].values[curr_base_idx]
                    join_feats_geom = join_feats['geometry'].values

                    if cover_col is not None:
                        join_geom_union = join_feats_geom.unary_union()
                        if in_cover_gdf is not None and cover_gdf[cover_col].values[curr_base_idx] > 0:
                            join_geom_union = join_geom_union.union(cover_gdf['geometry'].values[curr_base_idx])
                        join_geom_clip = join_geom_union.intersection(base_geom)
                        join_perc = float(join_geom_clip.area) / base_geom.area
                        if out_cover_gdf:
                            cover_gdf['geometry'].values[curr_base_idx] = join_geom_clip
                            cover_gdf[cover_col].values[curr_base_idx] = join_perc
                        base_gdf[cover_col].values[curr_base_idx] = join_perc

                    if out_raster_dir is not None:
                        raster_fname = get_raster_basename(base_gdf, curr_base_idx) + '.tif'
                        raster_file = os.path.join(out_raster_dir, raster_fname)
                        if base_geom.geometryType() == 'MultiPolygon':
                            base_geom_split = base_geom.geoms
                            if len(base_geom_split) == 1:
                                base_geom = base_geom_split[0]
                            else:
                                base_geom = base_geom.minimum_rotated_rectangle
                        coords_x, coords_y = base_geom.exterior.coords.xy
                        xmin, xmax = min(coords_x), max(coords_x)
                        ymin, ymax = min(coords_y), max(coords_y)
                        xsize = math.ceil((xmax-xmin) / raster_res)
                        ysize = math.ceil((ymax-ymin) / raster_res)
                        trans = rio.transform.from_origin(xmin, ymax, raster_res, raster_res)
                        count_array = rio.features.rasterize(
                            join_feats_geom,
                            out_shape=(ysize, xsize),
                            transform=trans,
                            merge_alg=rio.enums.MergeAlg.add,
                            default_value=1,
                            dtype=raster_dtype
                        )
                        with rio.open(
                                raster_file, 'w',
                                driver='GTiff', dtype=count_array.dtype,
                                height=count_array.shape[0], width=count_array.shape[1], count=1,
                                crs=base_gdf.crs, transform=trans,
                                nodata=raster_nodata, tiled=True, compress='lzw') as rio_ds:
                            rio_ds.write(count_array, 1)

                start_pos, curr_base_idx = end_pos, base_idx
                if show_progress:
                    bar()

    if how == 'inner':
        base_gdf = base_gdf.iloc[base_match_idx]
        if out_cover_gdf and cover_gdf is not None:
            cover_gdf = cover_gdf.iloc[base_match_idx]

    if base_gdf.crs != base_orig_crs:
        print("Reprojecting base GDF back to original base CRS")
        base_gdf = base_gdf.to_crs(base_orig_crs)

    if cover_gdf is not None and cover_gdf.crs != cover_orig_crs:
        print("Reprojecting cover GDF back to original CRS")
        cover_gdf = cover_gdf.to_crs(cover_orig_crs)

    outputs = []
    if out_spatial_index:
        outputs.append(spatial_index)
    outputs.append(base_gdf)
    if out_cover_gdf:
        outputs.append(cover_gdf)

    return outputs
