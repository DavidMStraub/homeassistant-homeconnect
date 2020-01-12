"""Constants for the Home Connect integration."""

DOMAIN = "homeconnect"

DEVICES = "DEVICES"

OAUTH2_AUTHORIZE = "https://api.home-connect.com/security/oauth/authorize"
OAUTH2_TOKEN = "https://api.home-connect.com/security/oauth/token"

BINARY_SENSORS_OFF_STATES = [
        "BSH.Common.EnumType.DoorState.Closed",
        "BSH.Common.EnumType.DoorState.Locked",
    ]
    
BINARY_SENSORS_ON_STATES = [
        "BSH.Common.EnumType.DoorState.Open",
    ]


SERVICE_STARTPROGRAM = "start_program"
SERVICE_STOPPROGRAM = "stop_program"
PROGRAM_NAMES = {
        "Cooking.Oven.Program.HeatingMode.HotAir": "hot_air",
        "Cooking.Oven.Program.HeatingMode.TopBottomHeating": "top_bottom_heating",
        "Cooking.Oven.Program.HeatingMode.HotAirEco": "hot_air_eco",
        "Cooking.Oven.Program.HeatingMode.TopBottomHeatingEco": "top_bottom_heating_eco",
        "Cooking.Oven.Program.HeatingMode.HotAirGrilling": "hot_air_grilling",
        "Cooking.Oven.Program.HeatingMode.PizzaSetting": "pizza_setting",
        "Cooking.Oven.Program.HeatingMode.SlowCook": "slow_cook",
        "Cooking.Oven.Program.HeatingMode.BottomHeating": "bottom_heating",
        "Cooking.Oven.Program.HeatingMode.Defrost": "defrost",
        "Cooking.Oven.Program.HeatingMode.KeepWarm": "keep_warm",
        "Cooking.Oven.Program.HeatingMode.PreheatOvenware": "preheat_ovenware",
    }
PROGRAM_OPTIONS = {
        "Cooking.Oven.Option.SetpointTemperature": "setpoint_temperature",
        "BSH.Common.Option.Duration": "duration",
        "BSH.Common.Option.StartInRelative": "start_in_relative",
        "Cooking.Oven.Option.FastPreHeat": "fast_pre_heat",
    }
