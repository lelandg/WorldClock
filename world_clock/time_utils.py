from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones
from zoneinfo import ZoneInfoNotFoundError

# On Windows, ensure tzdata is installed for zoneinfo database.
# If not present, zoneinfo may not find time zones. The user should install `tzdata`.


# Common timezone abbreviations mapped to representative IANA zones.
# Note: Abbreviations are ambiguous across regions; we pick widely-used defaults.
_TZ_ABBR_DEFAULT: dict[str, str] = {
    # North America
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "MST": "America/Denver",
    "MDT": "America/Denver",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "AKST": "America/Anchorage",
    "AKDT": "America/Anchorage",
    "HST": "Pacific/Honolulu",
    # Europe
    "GMT": "Etc/GMT",
    "UTC": "Etc/UTC",
    "WET": "Europe/Lisbon",
    "WEST": "Europe/Lisbon",
    "CET": "Europe/Paris",
    "CEST": "Europe/Paris",
    "EET": "Europe/Athens",
    "EEST": "Europe/Athens",
    "BST": "Europe/London",
    # Asia/Pacific
    "IST": "Asia/Kolkata",  # India Standard Time
    "JST": "Asia/Tokyo",
    "KST": "Asia/Seoul",
    "HKT": "Asia/Hong_Kong",
    "SGT": "Asia/Singapore",
    "AWST": "Australia/Perth",
    "ACST": "Australia/Adelaide",
    "AEST": "Australia/Sydney",
    "AEDT": "Australia/Sydney",
    "NZST": "Pacific/Auckland",
    "NZDT": "Pacific/Auckland",
    # Latin America
    "ART": "America/Argentina/Buenos_Aires",
    "BRT": "America/Sao_Paulo",
}


@dataclass(frozen=True)
class TimeZoneEntry:
    country: str  # ISO 3166-1 alpha-2 code, upper-case
    zone: str     # IANA timezone name


# Parse the IANA zone1970.tab content embedded below to map country codes to zones.
# This avoids external downloads and keeps mapping within the repo. The format is:
# CC\tCoordinates\tTimeZone\tComments
# For multiple country codes per zone, CC is like "US,CA".
# We only need CC and TimeZone columns.

_ZONE1970_TAB = r"""
# This file contains a table with the columns
# 1. country codes, 2. coordinates, 3. TZ database name, 4. comments.
# Lines beginning with '#' are comments.
AD	+4230+00131	Europe/Andorra
AE	+2518+05518	Asia/Dubai
AF	+3431+06912	Asia/Kabul
AG	+1703-06148	America/Antigua
AI	+1812-06304	America/Anguilla
AL	+4120+01950	Europe/Tirane
AM	+4011+04430	Asia/Yerevan
AO	-0848+01314	Africa/Luanda
AQ	-7750+16636	Antarctica/McMurdo	New Zealand time - McMurdo, South Pole
AQ	-6617+11031	Antarctica/Casey	Casey
AQ	-6835+07758	Antarctica/Davis	Davis
AQ	-6640+14001	Antarctica/DumontDUrville	Dumont d'Urville
AQ	-6736+06253	Antarctica/Mawson	Mawson
AQ	-6448-06406	Antarctica/Palmer	Palmer
AQ	-6734+08250	Antarctica/Rothera	Rothera
AQ	-690022+0393524	Antarctica/Syowa	Syowa
AQ	-720041+0023206	Antarctica/Troll	Troll
AQ	-7824+10654	Antarctica/Vostok	Vostok
AR	-3436-05827	America/Argentina/Buenos_Aires
AS	-1416-17042	Pacific/Pago_Pago
AT	+4813+01620	Europe/Vienna
AU	-3455+13835	Australia/Adelaide
AU	-3157+14127	Australia/Broken_Hill
AU	-4253+14719	Australia/Hobart
AU	-3749+14458	Australia/Melbourne
AU	-3157+11551	Australia/Perth
AU	-3332+15113	Australia/Sydney
AW	+1230-06958	America/Aruba
AX	+6006+01957	Europe/Mariehamn
AZ	+4023+04951	Asia/Baku
BA	+4352+01825	Europe/Sarajevo
BB	+1306-05937	America/Barbados
BD	+2343+09025	Asia/Dhaka
BE	+5050+00420	Europe/Brussels
BF	+1222-00131	Africa/Ouagadougou
BG	+4241+02319	Europe/Sofia
BH	+2623+05035	Asia/Bahrain
BI	-0323+02922	Africa/Bujumbura
BJ	+0629+00237	Africa/Porto-Novo
BL	+1753-06251	America/St_Barthelemy
BM	+3217-06446	Atlantic/Bermuda
BN	+0456+11455	Asia/Brunei
BO	-1630-06809	America/La_Paz
BQ	+1209-06817	America/Kralendijk
BR	-2332-04637	America/Sao_Paulo
BS	+2505-07721	America/Nassau
BT	+2728+08939	Asia/Thimphu
BW	-2439+02555	Africa/Gaborone
BY	+5354+02734	Europe/Minsk
BZ	+1730-08812	America/Belize
CA	+4339-07923	America/Toronto
CA	+4916-12307	America/Vancouver
CA	+5333-11328	America/Edmonton
CA	+4531-07334	America/Montreal
CA	+5321-07028	America/Moncton
CA	+4603-06447	America/Halifax
CA	+4439-06336	America/Glace_Bay
CA	+4901-08816	America/Nipigon
CA	+4843-09434	America/Winnipeg
CA	+6243-09210	America/Rankin_Inlet
CA	+6828-13343	America/Inuvik
CA	+6249-09205	America/Iqaluit
CA	+6344-06828	America/Pangnirtung
CA	+6900-10503	America/Coral_Harbour
CA	+6805-13503	America/Yellowknife
CA	+5333-11328	America/Edmonton
CA	+5334-11328	America/Whitehorse
CA	+5125-05707	America/Goose_Bay
CA	+7441-09449	America/Resolute
CA	+4824-08915	America/Thunder_Bay
CA	+6244-09208	America/Arviat
CA	+6825-11330	America/Tuktoyaktuk
CA	+6044-13503	America/Dawson
CC	-1210+09655	Indian/Cocos
CD	-0418+01518	Africa/Kinshasa
CD	-1140+02728	Africa/Lubumbashi
CF	+0422+01835	Africa/Bangui
CG	-0416+01517	Africa/Brazzaville
CH	+4723+00832	Europe/Zurich
CI	+0519-00402	Africa/Abidjan
CK	-2114-15946	Pacific/Rarotonga
CL	-3327-07040	America/Santiago
CM	+0403+00942	Africa/Douala
CN	+3946+11628	Asia/Shanghai
CO	+0436-07405	America/Bogota
CR	+0956-08405	America/Costa_Rica
CU	+2308-08222	America/Havana
CV	+1455-02331	Atlantic/Cape_Verde
CW	+1211-06900	America/Curacao
CX	-1025+10543	Indian/Christmas
CY	+3510+03322	Asia/Nicosia
CZ	+5005+01426	Europe/Prague
DE	+5230+01322	Europe/Berlin
DJ	+1136+04309	Africa/Djibouti
DK	+5540+01235	Europe/Copenhagen
DM	+1518-06124	America/Dominica
DO	+1828-06954	America/Santo_Domingo
DZ	+3647+00303	Africa/Algiers
EC	-0210-07950	America/Guayaquil
EC	-0055-08936	Pacific/Galapagos
EE	+5925+02445	Europe/Tallinn
EG	+3003+03115	Africa/Cairo
EH	+2709-01312	Africa/El_Aaiun
ER	+1520+03856	Africa/Asmara
ES	+4024-00341	Europe/Madrid
ES	+3553-00519	Atlantic/Canary
ET	+0902+03842	Africa/Addis_Ababa
FI	+6010+02458	Europe/Helsinki
FJ	-1808+17825	Pacific/Fiji
FK	-5142-05751	Atlantic/Stanley
FM	+0725+15147	Pacific/Chuuk
FO	+6201-00646	Atlantic/Faroe
FR	+4852+00220	Europe/Paris
GA	+0023+00927	Africa/Libreville
GB	+513030-0000731	Europe/London
GD	+1203-06145	America/Grenada
GE	+4143+04447	Asia/Tbilisi
GF	+0456-05220	America/Cayenne
GG	+492827-0023210	Europe/Guernsey
GH	+0533-00013	Africa/Accra
GI	+3608-00521	Europe/Gibraltar
GL	+6411-05144	America/Nuuk
GL	+7029-02158	America/Scoresbysund
GL	+7646-01840	America/Ittoqqortoormiit
GM	+1328-01639	Africa/Banjul
GN	+0931-01343	Africa/Conakry
GP	+1614-06132	America/Guadeloupe
GQ	+0325+00847	Africa/Malabo
GR	+3758+02343	Europe/Athens
GS	-5416-03632	Atlantic/South_Georgia
GT	+1438-09031	America/Guatemala
GU	+1328+14445	Pacific/Guam
GW	+1151-01535	Africa/Bissau
GY	+0648-05810	America/Guyana
HK	+2217+11409	Asia/Hong_Kong
HN	+1406-08713	America/Tegucigalpa
HR	+4548+01558	Europe/Zagreb
HT	+1832-07220	America/Port-au-Prince
HU	+4730+01905	Europe/Budapest
ID	-0610+10649	Asia/Jakarta
ID	-0507+11924	Asia/Makassar
ID	-0232+14042	Asia/Jayapura
IE	+5320-00615	Europe/Dublin
IL	+3146+03514	Asia/Jerusalem
IM	+5409-00428	Europe/Isle_of_Man
IN	+2232+08822	Asia/Kolkata
IO	-0720+07225	Indian/Chagos
IQ	+3321+04425	Asia/Baghdad
IR	+3540+05126	Asia/Tehran
IS	+6409-02151	Atlantic/Reykjavik
IT	+4154+01229	Europe/Rome
JE	+491130-0020620	Europe/Jersey
JM	+1800-07648	America/Jamaica
JO	+3157+03556	Asia/Amman
JP	+353916+1394441	Asia/Tokyo
KE	-0117+03649	Africa/Nairobi
KG	+4254+07436	Asia/Bishkek
KH	+1133+10455	Asia/Phnom_Penh
KI	+0125+17300	Pacific/Tarawa
KI	-0308-17105	Pacific/Enderbury
KI	+0152-15720	Pacific/Kiritimati
KM	-1142+04316	Indian/Comoro
KN	+1718-06243	America/St_Kitts
KP	+3901+12545	Asia/Pyongyang
KR	+3733+12658	Asia/Seoul
KW	+2920+04759	Asia/Kuwait
KY	+1918-08123	America/Cayman
KZ	+4315+07657	Asia/Almaty
KZ	+5030+08236	Asia/Qostanay
KZ	+5113+07126	Asia/Aqtobe
KZ	+4753+06727	Asia/Aqtau
KZ	+5312+06337	Asia/Atyrau
KZ	+5113+07126	Asia/Oral
LA	+1758+10236	Asia/Vientiane
LB	+3353+03530	Asia/Beirut
LC	+1401-06100	America/St_Lucia
LI	+4709+00931	Europe/Vaduz
LK	+0656+07951	Asia/Colombo
LR	+0618-01047	Africa/Monrovia
LS	-2928+02730	Africa/Maseru
LT	+5441+02519	Europe/Vilnius
LU	+4936+00609	Europe/Luxembourg
LV	+5657+02406	Europe/Riga
LY	+3254+01311	Africa/Tripoli
MA	+3339-00735	Africa/Casablanca
MC	+4342+00723	Europe/Monaco
MD	+4700+02850	Europe/Chisinau
ME	+4226+01916	Europe/Podgorica
MF	+1804-06305	America/Marigot
MG	-1855+04731	Indian/Antananarivo
MH	+0709+17112	Pacific/Majuro
MH	+0905+16720	Pacific/Kwajalein
MK	+4159+02126	Europe/Skopje
ML	+1239-00800	Africa/Bamako
MM	+1647+09610	Asia/Yangon
MN	+4755+10653	Asia/Ulaanbaatar
MN	+4804+11430	Asia/Choibalsan
MO	+2214+11335	Asia/Macau
MP	+1512+14545	Pacific/Saipan
MQ	+1436-06105	America/Martinique
MR	+1806-01557	Africa/Nouakchott
MS	+1643-06212	America/Montserrat
MT	+3554+01431	Europe/Malta
MU	-2010+05730	Indian/Mauritius
MV	+0410+07330	Indian/Maldives
MW	-1547+03500	Africa/Blantyre
MX	+1924-09909	America/Mexico_City
MX	+2058-08937	America/Merida
MX	+2540-10019	America/Monterrey
MX	+3103-11452	America/Tijuana
MY	+0310+10142	Asia/Kuala_Lumpur
MZ	-2558+03235	Africa/Maputo
NA	-2234+01706	Africa/Windhoek
NC	-2216+16627	Pacific/Noumea
NE	+1331+00207	Africa/Niamey
NF	-2903+16758	Pacific/Norfolk
NG	+0627+00324	Africa/Lagos
NI	+1209-08617	America/Managua
NL	+5222+00454	Europe/Amsterdam
NO	+5955+01045	Europe/Oslo
NP	+2743+08519	Asia/Kathmandu
NR	-0031+16655	Pacific/Nauru
NU	-1901-16955	Pacific/Niue
NZ	-3652+17446	Pacific/Auckland
NZ	-4357-17633	Pacific/Chatham
OM	+2336+05835	Asia/Muscat
PA	+0858-07932	America/Panama
PE	-1203-07703	America/Lima
PF	-1732-14934	Pacific/Tahiti
PF	-2308-13457	Pacific/Marquesas
PF	-0900-13930	Pacific/Gambier
PG	-0930+14710	Pacific/Port_Moresby
PH	+1435+12100	Asia/Manila
PK	+2452+06703	Asia/Karachi
PL	+5215+02100	Europe/Warsaw
PM	+4703-05620	America/Miquelon
PN	-2504-13005	Pacific/Pitcairn
PR	+182806-0660622	America/Puerto_Rico
PS	+3130+03428	Asia/Gaza
PS	+313200+0350542	Asia/Hebron
PT	+3843-00908	Europe/Lisbon
PT	+3238-01654	Atlantic/Madeira
PT	+3744-02540	Atlantic/Azores
PW	+0720+13429	Pacific/Palau
PY	-2516-05740	America/Asuncion
QA	+2517+05132	Asia/Qatar
RE	-2052+05528	Indian/Reunion
RO	+4426+02606	Europe/Bucharest
RS	+4450+02030	Europe/Belgrade
RU	+5545+03735	Europe/Moscow
RU	+5500+07324	Asia/Novosibirsk
RU	+4844+04425	Europe/Volgograd
RU	+5903+03851	Europe/Kirov
RU	+6200+12940	Asia/Yakutsk
RU	+6010+15110	Asia/Vladivostok
RU	+5312+15824	Asia/Magadan
RU	+4310+13156	Asia/Vladivostok
RW	-0157+03004	Africa/Kigali
SA	+2438+04643	Asia/Riyadh
SB	-0932+16012	Pacific/Guadalcanal
SC	-0440+05528	Indian/Mahe
SD	+1536+03232	Africa/Khartoum
SE	+5920+01803	Europe/Stockholm
SG	+0117+10351	Asia/Singapore
SH	-1555-00542	Atlantic/St_Helena
SI	+4603+01431	Europe/Ljubljana
SJ	+7800+01600	Arctic/Longyearbyen
SK	+4809+01707	Europe/Bratislava
SL	+0830-01315	Africa/Freetown
SM	+4355+01228	Europe/San_Marino
SN	+1440-01726	Africa/Dakar
SO	+0204+04522	Africa/Mogadishu
SR	+0550-05510	America/Paramaribo
SS	+0451+03137	Africa/Juba
ST	+0020+00644	Africa/Sao_Tome
SV	+1342-08912	America/El_Salvador
SX	+1803-06303	America/Lower_Princes
SY	+3330+03618	Asia/Damascus
SZ	-2618+03106	Africa/Mbabane
TC	+2128-07108	America/Grand_Turk
TD	+1207+01503	Africa/Ndjamena
TF	-492110+0701303	Indian/Kerguelen
TG	+0608-00113	Africa/Lome
TH	+1345+10031	Asia/Bangkok
TJ	+3835+06848	Asia/Dushanbe
TK	-0922-17114	Pacific/Fakaofo
TL	-0833+12535	Asia/Dili
TM	+3757+05823	Asia/Ashgabat
TN	+3648+01011	Africa/Tunis
TO	-2110-17510	Pacific/Tongatapu
TR	+4101+02858	Europe/Istanbul
TT	+1039-06131	America/Port_of_Spain
TV	-0831+17913	Pacific/Funafuti
TW	+2503+12130	Asia/Taipei
TZ	-0648+03917	Africa/Dar_es_Salaam
UA	+5026+03031	Europe/Kyiv
UG	+0019+03225	Africa/Kampala
UM	+1645-16931	Pacific/Johnston
UM	+2813-17722	Pacific/Midway
UM	+2813-17722	Pacific/Wake
US	+404251-0740023	America/New_York
US	+341308-1181434	America/Los_Angeles
US	+290951-0950949	America/Chicago
US	+394421-1045903	America/Denver
US	+3757-12225	America/Los_Angeles
US	+471659-1222019	America/Los_Angeles
US	+332654-1120424	America/Phoenix
US	+4403-12305	America/Los_Angeles
US	+4506-06606	America/Halifax
UY	-3453-05611	America/Montevideo
UZ	+3940+06648	Asia/Tashkent
VA	+4154+01227	Europe/Vatican
VC	+1309-06114	America/St_Vincent
VE	+1030-06656	America/Caracas
VG	+1827-06437	America/Tortola
VI	+1821-06456	America/St_Thomas
VN	+1045+10640	Asia/Ho_Chi_Minh
VU	-1740+16825	Pacific/Efate
WF	-1318-17610	Pacific/Wallis
WS	-1350-17144	Pacific/Apia
YE	+1245+04512	Asia/Aden
YT	-1247+04514	Indian/Mayotte
ZA	-2615+02800	Africa/Johannesburg
ZM	-1525+02817	Africa/Lusaka
ZW	-1750+03103	Africa/Harare
"""


def load_country_timezones() -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for line in _ZONE1970_TAB.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) < 3:
            continue
        cc_part = parts[0]
        tz = parts[2]
        for cc in cc_part.split(','):
            cc = cc.upper()
            mapping.setdefault(cc, [])
            if tz not in mapping[cc]:
                mapping[cc].append(tz)
    return mapping


_COUNTRY_TZ = load_country_timezones()


def normalize_country_code(code: str) -> str:
    return code.strip().upper()


def has_tz_database() -> bool:
    try:
        return len(available_timezones()) > 0
    except Exception:
        return False


def get_timezones_for_country(code: str, include_all: bool = True) -> list[str]:
    code = normalize_country_code(code)
    zones = _COUNTRY_TZ.get(code, [])
    # Filter zones to those available in current zoneinfo database (if any)
    try:
        avail = available_timezones()
    except Exception:
        avail = set()
    if avail:
        zones = [z for z in zones if z in avail]
    if not zones:
        return []
    if include_all:
        return zones
    # Choose a representative one
    return [zones[0]]


def get_timezones_for_input(token: str, include_all: bool = True) -> list[str]:
    """
    Resolve a user-provided token to one or more IANA time zone names.
    Accepted inputs:
      - ISO country codes (alpha-2), e.g., US, IN
      - IANA time zone names, e.g., America/Chicago
      - Common abbreviations, e.g., CST, EST, IST (mapped to defaults)
    """
    if not token:
        return []

    # Try as country code first
    cc = normalize_country_code(token)
    if len(cc) == 2 and cc.isalpha():
        zones = get_timezones_for_country(cc, include_all=include_all)
        if zones:
            return zones

    # Try as full IANA zone name
    tz_name = token.strip()
    try:
        # This will raise if not found
        ZoneInfo(tz_name)
        return [tz_name]
    except Exception:
        pass

    # Try as abbreviation
    abbr = token.strip().upper()
    mapped = _TZ_ABBR_DEFAULT.get(abbr)
    if mapped:
        try:
            ZoneInfo(mapped)
            return [mapped]
        except Exception:
            return []

    # Not recognized
    return []


def now_in_zone(zone: str) -> datetime:
    try:
        return datetime.now(ZoneInfo(zone))
    except ZoneInfoNotFoundError:
        raise RuntimeError(
            "Time zone database not found. Please install the 'tzdata' package (e.g., pip install tzdata) to enable DST-aware time zones on this system."
        )


def format_time(dt: datetime, show_seconds: bool = True) -> str:
    return dt.strftime('%Y-%m-%d %H:%M:%S' if show_seconds else '%Y-%m-%d %H:%M')
