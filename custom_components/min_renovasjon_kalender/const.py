"""Constants for the Min Renovasjon Kalender integration."""

DOMAIN = "min_renovasjon_kalender"
NAME = "Min Renovasjon Kalender"
VERSION = "1.0.0"

# Config entry data keys
CONF_STREET_NAME = "street_name"
CONF_STREET_CODE = "street_code"
CONF_HOUSE_NO = "house_no"
CONF_COUNTY_ID = "county_id"

# Options keys
CONF_CALENDAR_DAYS = "calendar_days"
DEFAULT_CALENDAR_DAYS = 365
CONF_CALENDAR_DAYS_BACK = "calendar_days_back"
DEFAULT_CALENDAR_DAYS_BACK = 30
CONF_EXCLUDED_FRACTION_IDS = "excluded_fraction_ids"

# API constants
CONST_KOMMUNE_NUMMER = "Kommunenr"
CONST_APP_KEY = "RenovasjonAppKey"
CONST_APP_KEY_VALUE = "AE13DEEC-804F-4615-A74E-B4FAC11F0A30"

ADDRESS_LOOKUP_URL = "https://ws.geonorge.no/adresser/v1/sok?"
APP_CUSTOMERS_URL = (
    "https://www.webatlas.no/wacloud/servicerepository/"
    "CatalogueService.svc/json/GetRegisteredAppCustomers"
)
KOMTEK_API_BASE_URL = "https://norkartrenovasjon.azurewebsites.net/proxyserver.ashx"
CONST_URL_FRAKSJONER = (
    f"{KOMTEK_API_BASE_URL}"
    "?server=https://komteksky.norkart.no/MinRenovasjon.Api/api/fraksjoner"
)
CONST_URL_TOMMEKALENDER = (
    f"{KOMTEK_API_BASE_URL}"
    "?server=https://komteksky.norkart.no/MinRenovasjon.Api/api/tommekalender/"
    "?gatenavn=[gatenavn]&gatekode=[gatekode]&husnr=[husnr]"
    "&fraDato=[fra_dato]&dato=[til_dato]&api-version=2"
)
