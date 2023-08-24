"""Example implementation of the psutils.regex module
"""

import math
import re
from collections import OrderedDict

import psutils.custom_errors as cerr
import psutils.regex as psu_re
from psutils.versionstring import VersionString


class SetsmVersionKey(psu_re.Regex):
    regrp_major = 'major'
    regrp_minor = 'minor'
    regrp_patch = 'patch'
    restr = r"v(?P<%s>\d{2})(?P<%s>\d{2})(?P<%s>\d{2})" % (regrp_major, regrp_minor, regrp_patch)
    recmp = re.compile(restr)
    def __init__(self, string_or_match=None, re_function=psu_re.RE_FULLMATCH_FN, **re_function_kwargs):
        super(SetsmVersionKey, self).__init__(string_or_match, re_function, **re_function_kwargs)
    def _populate_match(self, re_match):
        super(SetsmVersionKey, self)._populate_match(re_match)
        if self.matched:
            self.SetsmVersionKey = self
            self.verkey          = self.match_str
            self.major           = int(self.groupdict[SetsmVersionKey.regrp_major])
            self.minor           = int(self.groupdict[SetsmVersionKey.regrp_minor])
            self.patch           = int(self.groupdict[SetsmVersionKey.regrp_patch])
            self.version         = VersionString('.'.join([str(num) for num in [self.major, self.minor, self.patch]]))
    def _reset_match_attributes(self):
        super(SetsmVersionKey, self)._reset_match_attributes()
        self.SetsmVersionKey = None
        self.verkey          = None
        self.major           = None
        self.minor           = None
        self.patch           = None
        self.version         = None


def SetsmVersion(version):
    accepted_version_types = (str, float, int, SetsmVersionKey, VersionString)
    version_key = None
    version_string = None
    version_type = type(version)
    if version_type in (str, float, int):
        if version_type is str and version.startswith('v'):
            verkey_str = version
            version_key = SetsmVersionKey(verkey_str, psu_re.RE_FULLMATCH_FN)
            if not version_key.matched:
                raise cerr.InvalidArgumentError(
                    "Failed to parse `version` argument ('{}') with {} regex ('{}')".format(
                        version, SetsmVersionKey, SetsmVersionKey.restr
                    )
                )
        else:
            version_string = VersionString(version, nelements=3)
    elif isinstance(version, SetsmVersionKey):
        version_key = version
    elif isinstance(version, VersionString):
        version_string = VersionString(version.string, nelements=3)
    else:
        raise cerr.InvalidArgumentError("`version` type must be one of {}, but was {}".format(
            accepted_version_types, version
        ))
    if version_key is None:
        assert version_string is not None
        if len(version_string.nums) != 3:
            raise cerr.InvalidArgumentError(
                "`version` {} argument must have three elements (major, minor, patch), "
                "but has {} elements: '{}'".format(
                    VersionString, len(version_string.nums), version_string.string
                )
            )
        if not all([0 <= n <= 99 for n in version_string.nums]):
            raise cerr.InvalidArgumentError(
                "`version` {} argument element values (major, minor, patch) "
                "must be in the range [0, 99]: '{}'".format(
                    VersionString, version_string.string
                )
            )
        verkey_str = 'v{}'.format(''.join(['{:0>2}'.format(n) for n in version_string.nums]))
        version_key = SetsmVersionKey(verkey_str, psu_re.RE_FULLMATCH_FN)
        if not version_key.matched:
            raise cerr.InvalidArgumentError(
                "Failed to parse {} '{}' into {} object".format(
                    VersionString, version, SetsmVersionKey
                )
            )
    return version_key


class DemResName(psu_re.Regex):
    regrp_value = 'value'
    regrp_unit = 'unit'
    unit_m = 'm'
    unit_cm = 'cm'
    restr = r"(?P<%s>\d+)(?P<%s>%s|%s)" % (regrp_value, regrp_unit, unit_m, unit_cm)
    recmp = re.compile(restr)
    def __init__(self, string_or_match=None, re_function=psu_re.RE_FULLMATCH_FN, **re_function_kwargs):
        super(DemResName, self).__init__(string_or_match, re_function, **re_function_kwargs)
    def _populate_match(self, re_match):
        super(DemResName, self)._populate_match(re_match)
        if self.matched:
            self.DemResName = self
            self.res_name   = self.match_str
            self.value      = self.groupdict[DemResName.regrp_value]
            self.unit       = self.groupdict[DemResName.regrp_unit]
    def _reset_match_attributes(self):
        super(DemResName, self)._reset_match_attributes()
        self.DemResName = None
        self.res_name   = None
        self.value      = None
        self.unit       = None


class DemRes(object):

    accepted_res_types = (str, float, int, DemResName)
    accepted_res_name_types = (str, DemResName)
    standard_res_meters = (0.5, 1, 2, 8)

    def __init__(self, res, allow_nonstandard_res=False):
        res_name = None
        res_meters = None
        res_whole_meters = None
        res_type = type(res)
        if res_type is str:
            try:
                res_str_as_float = float(res)
                try:
                    res_str_as_int = int(res)
                    res_whole_meters = res_str_as_int
                except ValueError:
                    res_meters = res_str_as_float
            except ValueError:
                res_name = res
        elif res_type is float:
            res_meters = res
        elif res_type is int:
            res_whole_meters = res
        elif isinstance(res, DemResName):
            res_name = res
        else:
            raise cerr.InvalidArgumentError("`res` type must be one of {}, but was {}".format(
                DemRes.accepted_res_types, res_type
            ))
        self.name, self.meters, self.whole_meters = self.get_res_forms(
            res_name, res_meters, res_whole_meters, allow_nonstandard_res
        )

    @staticmethod
    def get_res_forms(res_name=None, res_meters=None, res_whole_meters=None,
                      allow_nonstandard_res=False):
        if not any([arg is not None for arg in [res_name, res_meters, res_whole_meters]]):
            raise cerr.InvalidArgumentError("At least one resolution argument must be provided")

        if res_meters is not None:
            res_meters = float(res_meters)
        converted_res_meters = None

        if res_name is not None:
            res_name_type = type(res_name)
            if res_name_type is str:
                dem_res_name = DemResName(res_name, psu_re.RE_FULLMATCH_FN)
                if not dem_res_name.matched:
                    raise cerr.InvalidArgumentError(
                        "Failed to parse `res_name` argument ('{}') with {} regex ('{}')".format(
                        res_name, DemResName, DemResName.restr
                    ))
            elif isinstance(res_name, DemResName):
                dem_res_name = res_name
            else:
                raise cerr.InvalidArgumentError("`res_name` type must be one of {}, but was {}".format(
                    DemRes.accepted_res_name_types, res_name_type
                ))
            res_name = dem_res_name.string
            if dem_res_name.unit == DemResName.unit_m:
                converted_res_meters = float(dem_res_name.value)
            elif dem_res_name.unit == DemResName.unit_cm:
                converted_res_meters = float(dem_res_name.value) / 100
            if res_meters is None:
                res_meters = converted_res_meters
            elif res_meters != converted_res_meters:
                raise cerr.InvalidArgumentError(
                    "Mismatch between converted res meters ({}) from `res_name` argument ('{}') "
                    "and `res_meters` argument ({}) ".format(
                        converted_res_meters, res_name, res_meters,
                    )
                )

        if res_whole_meters is not None:
            res_whole_meters_as_int = int(res_whole_meters)
            if res_whole_meters_as_int != res_whole_meters:
                raise cerr.InvalidArgumentError(
                    "`res_whole_meters_as_int` argument must be convertible to an integer, "
                    "but was {}".format(res_whole_meters)
                )
            res_whole_meters = res_whole_meters_as_int
            converted_res_meters = 0.5 if res_whole_meters == 0 else float(res_whole_meters)
            if res_meters is None:
                res_meters = converted_res_meters
            elif res_meters != converted_res_meters:
                raise cerr.InvalidArgumentError(
                    "Mismatch between converted res meters ({}) from `res_whole_meters` argument ('{}') "
                    "and other resolution argument(s)".format(
                        converted_res_meters, res_whole_meters,
                    )
                )

        if res_meters <= 0:
            raise cerr.InvalidArgumentError("Resolution in meters must be > 0, but was {}".format(res_meters))
        if not allow_nonstandard_res and res_meters not in DemRes.standard_res_meters:
            raise cerr.InvalidArgumentError("Resolution in meters must be one of standard set {}, "
                                            "but was {}".format(DemRes.standard_res_meters, res_meters))

        if res_whole_meters is None:
            res_whole_meters = int(math.floor(res_meters))
        if res_name is None:
            if res_meters == res_whole_meters:
                res_name = '{}m'.format(int(res_meters))
            else:
                res_name = '{}cm'.format(int(math.floor(res_meters * 100)))

        return res_name, res_meters, res_whole_meters


RECMP_CATALOGID = re.compile("[0-9A-F]{16}")


class Pairname(psu_re.Regex):
    regrp_sensor, recmp_sensor = 'sensor', re.compile("[A-Z][A-Z0-9]{2}[0-9]")
    regrp_timestamp, recmp_timestamp = 'timestamp', re.compile("\d{8}")
    regrp_catid1, recmp_catid1 = 'catid1', RECMP_CATALOGID
    regrp_catid2, recmp_catid2 = 'catid2', RECMP_CATALOGID
    @staticmethod
    def construct(sensor=None, timestamp=None, catid1=None, catid2=None,
                  validate=True, return_regex=False):
        skip_inspection = False
        if all([sensor, timestamp, catid1, catid2]):
            if not validate:
                skip_inspection = True
        elif not return_regex:
            raise cerr.InvalidArgumentError(
                "All regex group values must be provided when `return_regex=False`"
            )
        regrp_setting_dict = OrderedDict([
            (Pairname.regrp_sensor,      [sensor,    Pairname.recmp_sensor]),
            (Pairname.regrp_timestamp,   [timestamp, Pairname.recmp_timestamp]),
            (Pairname.regrp_catid1,      [catid1,    Pairname.recmp_catid1]),
            (Pairname.regrp_catid2,      [catid2,    Pairname.recmp_catid2]),
        ])
        if not skip_inspection:
            try:
                for regrp, setting in regrp_setting_dict.items():
                    arg_string, default_recmp = setting
                    if arg_string is None:
                        setting[0] = default_recmp.pattern
                    elif validate and not psu_re.RE_FULLMATCH_FN(default_recmp, arg_string):
                        raise psu_re.RegexConstructionFailure(regrp, arg_string, default_recmp.pattern)
            except psu_re.RegexConstructionFailure:
                if not return_regex:
                    return None
                else:
                    raise
        if return_regex:
            full_restr = '_'.join([
                "(?P<{}>{})".format(regrp, setting[0])
                for regrp, setting in regrp_setting_dict.items()
            ])
            return full_restr
        else:
            full_string = '_'.join([setting[0] for setting in regrp_setting_dict.values()])
            return full_string
    @staticmethod
    def get_regex(sensor=None, timestamp=None, catid1=None, catid2=None, validate=True):
        return Pairname.construct(sensor, timestamp, catid1, catid2, validate, True)
    def __init__(self, string_or_match=None, re_function=psu_re.RE_FULLMATCH_FN,
                 sensor=None,
                 timestamp=None,
                 catid1=None,
                 catid2=None,
                 **re_function_kwargs):
        if any([sensor, timestamp, catid1, catid2]):
            self.restr = self.get_regex(sensor, timestamp, catid1, catid2)
            self.recmp = re.compile(self.restr)
        super(Pairname, self).__init__(string_or_match, re_function, **re_function_kwargs)
    def _populate_match(self, re_match):
        super(Pairname, self)._populate_match(re_match)
        if self.matched:
            self.Pairname   = self
            self.pairname   = self.match_str
            self.sensor     = self.groupdict[Pairname.regrp_sensor]
            self.timestamp  = self.groupdict[Pairname.regrp_timestamp]
            self.catid1     = self.groupdict[Pairname.regrp_catid1]
            self.catid2     = self.groupdict[Pairname.regrp_catid2]
            self.catids     = [self.catid1, self.catid2]
    def _reset_match_attributes(self):
        super(Pairname, self)._reset_match_attributes()
        self.Pairname   = None
        self.pairname   = None
        self.sensor     = None
        self.timestamp  = None
        self.catid1     = None
        self.catid2     = None
        self.catids     = None
Pairname.restr = Pairname.get_regex()
Pairname.recmp = re.compile(Pairname.restr)


class PartID(psu_re.Regex):
    regrp_tilenum,  recmp_tilenum  = 'tilenum',  re.compile("R\d+C\d+")
    regrp_ordernum, recmp_ordernum = 'ordernum', re.compile("\d{12}_\d{2}")
    regrp_partnum,  recmp_partnum  = 'partnum',  re.compile("P\d{3}")
    @staticmethod
    def construct(ordernum=None, tilenum=None, partnum=None,
                  validate=True, return_regex=False):
        skip_inspection = False
        if all([ordernum, tilenum, partnum]):
            if not validate:
                skip_inspection = True
        elif not return_regex:
            raise cerr.InvalidArgumentError(
                "All regex group values must be provided when `return_regex=False`"
            )
        regrp_setting_dict = OrderedDict([
            (PartID.regrp_tilenum,     [tilenum,  PartID.recmp_tilenum]),
            (PartID.regrp_ordernum,    [ordernum, PartID.recmp_ordernum]),
            (PartID.regrp_partnum,     [partnum,  PartID.recmp_partnum]),
        ])
        if not skip_inspection:
            try:
                for regrp, setting in regrp_setting_dict.items():
                    arg_string, default_recmp = setting
                    if arg_string is None:
                        setting[0] = default_recmp.pattern
                    elif validate and not psu_re.RE_FULLMATCH_FN(default_recmp, arg_string):
                        raise psu_re.RegexConstructionFailure(regrp, arg_string, default_recmp.pattern)
            except psu_re.RegexConstructionFailure:
                if not return_regex:
                    return None
                else:
                    raise
        if return_regex:
            full_restr = "(?:{}-)?{}_{}".format(*[
                "(?P<{}>{})".format(regrp, setting[0])
                for regrp, setting in regrp_setting_dict.items()
            ])
            return full_restr
        else:
            full_string = "{}{}".format(
                tilenum+'-' if tilenum is not None else '',
                '_'.join([setting[0] for setting in regrp_setting_dict.values()
                          if setting[1] is not PartID.recmp_tilenum])
            )
            return full_string
    @staticmethod
    def get_regex(tilenum=None, ordernum=None, partnum=None, validate=True):
        return PartID.construct(tilenum, ordernum, partnum, validate, True)
    def __init__(self, string_or_match=None, re_function=psu_re.RE_FULLMATCH_FN,
                 ordernum=None,
                 tilenum=None,
                 partnum=None,
                 **re_function_kwargs):
        if any([ordernum, tilenum, partnum]):
            self.restr = self.get_regex(ordernum, tilenum, partnum)
            self.recmp = re.compile(self.restr)
        super(PartID, self).__init__(string_or_match, re_function, **re_function_kwargs)
    def _populate_match(self, re_match):
        super(PartID, self)._populate_match(re_match)
        if self.matched:
            self.PartID   = self
            self.partid   = self.match_str
            self.tilenum  = self.groupdict[PartID.regrp_tilenum]
            self.ordernum = self.groupdict[PartID.regrp_ordernum]
            self.partnum  = self.groupdict[PartID.regrp_partnum]
    def PartID(self):
        super(PartID, self)._reset_match_attributes()
        self.PartID   = None
        self.partid   = None
        self.tilenum  = None
        self.ordernum = None
        self.partnum  = None
PartID.restr = PartID.get_regex()
PartID.recmp = re.compile(PartID.restr)


class SceneDemOverlapID(psu_re.Regex):
    regrp_pairname = 'pairname'
    regrp_partid1 = 'partid1'
    regrp_partid2 = 'partid2'
    restr = r"(?P<%s>{0})_(?P<%s>{1})_(?P<%s>{1})" % (regrp_pairname, regrp_partid1, regrp_partid2)
    restr = restr.format(Pairname.recmp.pattern, PartID.recmp.pattern)
    recmp = re.compile(restr)
    def __init__(self, string_or_match=None, re_function=psu_re.RE_FULLMATCH_FN, **re_function_kwargs):
        super(SceneDemOverlapID, self).__init__(string_or_match, re_function, **re_function_kwargs)
    def _populate_match(self, re_match):
        super(SceneDemOverlapID, self)._populate_match(re_match)
        if self.matched:
            self.SceneDemOverlapID = self
            self.sceneDemOverlapID = self.match_str
            self.pairname          = self.groupdict[SceneDemOverlapID.regrp_pairname]
            self.Pairname          = Pairname(self.re_match)
            self.partid1           = self.groupdict[SceneDemOverlapID.regrp_partid1]
            self.PartID1           = PartID(self.partid1)
            self.partid2           = self.groupdict[SceneDemOverlapID.regrp_partid2]
            self.PartID2           = PartID(self.partid2)
            self.ordernum1         = self.PartID1.ordernum
            self.ordernum2         = self.PartID2.ordernum
            self.ordernums         = [self.ordernum1, self.ordernum2]
    def _reset_match_attributes(self):
        super(SceneDemOverlapID, self)._reset_match_attributes()
        self.SceneDemOverlapID = None
        self.sceneDemOverlapID = None
        self.pairname          = None
        self.Pairname          = None
        self.partid1           = None
        self.PartID1           = None
        self.partid2           = None
        self.PartID2           = None
        self.ordernum1         = None
        self.ordernum2         = None
        self.ordernums         = None


class SceneDemID(psu_re.Regex):
    regrp_sceneDemOverlapID = 'sceneDemOverlapID'
    regrp_res = 'res'
    regrp_subtile = 'subtile'
    restr = ''.join([
        r"(?P<%s>{0})_" % regrp_sceneDemOverlapID,
        r"(?P<%s>\d{{1}})(?P<%s>-\d{{2}})?" % (regrp_res, regrp_subtile)
    ])
    restr = restr.format(SceneDemOverlapID.recmp.pattern)
    recmp = re.compile(restr)
    def __init__(self, string_or_match=None, re_function=psu_re.RE_FULLMATCH_FN, **re_function_kwargs):
        super(SceneDemID, self).__init__(string_or_match, re_function, **re_function_kwargs)
    def _populate_match(self, re_match):
        super(SceneDemID, self)._populate_match(re_match)
        if self.matched:
            self.SceneDemID        = self
            self.sceneDemID        = self.match_str
            self.sceneDemOverlapID = self.groupdict[SceneDemID.regrp_sceneDemOverlapID]
            self.SceneDemOverlapID = SceneDemOverlapID(self.re_match)
            self.pairname          = self.groupdict[SceneDemOverlapID.regrp_pairname]
            self.Pairname          = Pairname(self.re_match)
            self.partid1           = self.groupdict[SceneDemOverlapID.regrp_partid1]
            self.PartID1           = PartID(self.partid1)
            self.partid2           = self.groupdict[SceneDemOverlapID.regrp_partid2]
            self.PartID2           = PartID(self.partid2)
            self.ordernum1         = self.PartID1.ordernum
            self.ordernum2         = self.PartID2.ordernum
            self.ordernums         = [self.ordernum1, self.ordernum2]
            self.res               = self.groupdict[SceneDemID.regrp_res]
            self.DemRes            = DemRes(self.res)
            self.subtile           = self.groupdict[SceneDemID.regrp_subtile]
    def _reset_match_attributes(self):
        super(SceneDemID, self)._reset_match_attributes()
        self.SceneDemID        = None
        self.sceneDemID        = None
        self.SceneDemOverlapID = None
        self.pairname          = None
        self.Pairname          = None
        self.partid1           = None
        self.PartID1           = None
        self.partid2           = None
        self.PartID2           = None
        self.ordernum1         = None
        self.ordernum2         = None
        self.ordernums         = None
        self.res               = None
        self.DemRes            = None
        self.subtile           = None


class StripSegmentID(psu_re.Regex):
    regrp_pairname = 'pairname'
    regrp_res = 'res'
    regrp_lsf = 'lsf'
    regrp_segnum = 'segnum'
    restr = r"(?P<%s>{0})_(?P<%s>{1})(?:_(?P<%s>lsf))?_seg(?P<%s>\d+)" % (
        regrp_pairname, regrp_res, regrp_lsf, regrp_segnum
    )
    restr = restr.format(Pairname.recmp.pattern, DemResName.recmp.pattern)
    recmp = re.compile(restr)
    def __init__(self, string_or_match=None, re_function=psu_re.RE_FULLMATCH_FN, **re_function_kwargs):
        super(StripSegmentID, self).__init__(string_or_match, re_function, **re_function_kwargs)
    def _populate_match(self, re_match):
        super(StripSegmentID, self)._populate_match(re_match)
        if self.matched:
            self.StripSegmentID = self
            self.stripSegmentID = self.match_str
            self.pairname       = self.groupdict[StripSegmentID.regrp_pairname]
            self.Pairname       = Pairname(self.re_match)
            self.res            = self.groupdict[StripSegmentID.regrp_res]
            self.DemRes         = DemRes(self.res)
            self.lsf            = self.groupdict[StripSegmentID.regrp_lsf]
            self.segnum         = self.groupdict[StripSegmentID.regrp_segnum]
    def _reset_match_attributes(self):
        super(StripSegmentID, self)._reset_match_attributes()
        self.StripSegmentID = None
        self.stripSegmentID = None
        self.pairname       = None
        self.Pairname       = None
        self.res            = None
        self.DemRes         = None
        self.lsf            = None
        self.segnum         = None


class StripDemID(psu_re.Regex):
    regrp_pairname = 'pairname'
    regrp_res = 'res'
    regrp_verkey = 'verkey'
    restr = r"(?P<%s>{0})_(?P<%s>{1})_(?P<%s>{2})" % (
        regrp_pairname, regrp_res, regrp_verkey
    )
    restr = restr.format(Pairname.recmp.pattern, DemResName.recmp.pattern, SetsmVersionKey.recmp.pattern)
    recmp = re.compile(restr)
    def __init__(self, string_or_match=None, re_function=psu_re.RE_FULLMATCH_FN, **re_function_kwargs):
        super(StripDemID, self).__init__(string_or_match, re_function, **re_function_kwargs)
    def _populate_match(self, re_match):
        super(StripDemID, self)._populate_match(re_match)
        if self.matched:
            self.stripDemID = self.match_str
            self.pairname   = self.groupdict[StripDemID.regrp_pairname]
            self.Pairname   = Pairname(self.re_match)
            self.res        = self.groupdict[StripDemID.regrp_res]
            self.DemRes     = DemRes(self.res)
            self.verkey     = self.groupdict[StripDemFolder.regrp_verkey]
            self.Verkey     = SetsmVersionKey(self.re_match)
            self.version    = self.Verkey.version
    def _reset_match_attributes(self):
        super(StripDemID, self)._reset_match_attributes()
        self.stripDemID = None
        self.pairname   = None
        self.Pairname   = None
        self.res        = None
        self.DemRes     = None
        self.version    = None
        self.Verkey     = None
        self.version    = None


class StripDemFolder(psu_re.Regex):
    regrp_pairname = 'pairname'
    regrp_res = 'res'
    regrp_lsf = 'lsf'
    regrp_verkey = 'verkey'
    restr = r"(?P<%s>{0})_(?P<%s>{1})(?:_(?P<%s>lsf))?_(?P<%s>{2})" % (
        regrp_pairname, regrp_res, regrp_lsf, regrp_verkey
    )
    restr = restr.format(Pairname.recmp.pattern, DemResName.recmp.pattern, SetsmVersionKey.recmp.pattern)
    recmp = re.compile(restr)
    def __init__(self, string_or_match=None, re_function=psu_re.RE_FULLMATCH_FN, **re_function_kwargs):
        super(StripDemFolder, self).__init__(string_or_match, re_function, **re_function_kwargs)
    def _populate_match(self, re_match):
        super(StripDemFolder, self)._populate_match(re_match)
        if self.matched:
            self.StripDemFolder = self
            self.stripDemFolder = self.match_str
            self.StripDemID     = StripDemID.construct(
                pairname=self.groupdict[StripDemFolder.regrp_pairname],
                res     =self.groupdict[StripDemFolder.regrp_res],
                version =self.groupdict[StripDemFolder.regrp_verkey]
            )
            self.lsf            = self.groupdict[StripDemFolder.regrp_lsf]

    def _reset_match_attributes(self):
        super(StripDemFolder, self)._reset_match_attributes()
        self.StripDemFolder = None
        self.stripDemFolder = None
        self.StripDemID     = None
        self.lsf            = None
