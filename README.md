# Dreame Furcatch FP10 Air Purifier Integration for Home Assistant

Custom Home Assistant integration for the **Dreame Furcatch FP10 Air Purifier** (model `dreame.airp.u2513`), built by reverse-engineering the Dreame Cloud API.

## Features

### Fan Entity
- **Power on/off** — switches between running and standby state
- **Mode** — Auto, Sleep, Custom, Pet
- **Fan speed** — 10 speed levels (1-10) (shown as 10/20/30/40/50/60/70/80/90/100% in HA)
    - Setting fan speed automatically switches to Custom mode

### Sensors
- **Power** = shows main state of device (standby/running)
- **PM2.5** — Real-time particulate matter reading (µg/m³)
- **AQ** — Numeric (1-4) air quality index from the device, where 1 is excellent, and 4 is poor
- **Temperature** = Temp sensor (C/F)
- **Humidity** - Humidity sensor (0-100%)
- **TVOC** - Total Volatile Organic Compounds (µg/m³)
- **Filter Life** — Remaining filter durability (100-0%)
- **Filter Remaining Days** — Days remaining until filter change
- **Hair Collection Box Life** — Remaining until box cleaning (100-0%)
- **Hair Collection Box Remaining Days** — Days remaining until box cleaning

### Other entities
- **Ambient Light** — Sets ambient light brightness and breathing mode
- **Buzzer** — Toggle button sounds
- **Child Lock** — Toggle the child lock
- **Timer** - sets timer to 0-12 hours
- **Filter self cleaning** - starts self cleaning procedure
- **Temperature unit** - sets temperature unit to C or F
- **Weight unit** - sets weight unit to kg or lb

## Installation

### Via HACS (Recommended)

1. In Home Assistant: **HACS → Integrations**
2. Click **⋮** (top right) → **Custom repositories**
3. Paste URL: `<placeholder>`
4. Category: **Integration** → **Add**
5. Search **"Dreame Furcatch FP10"** → **Download** → restart HA
6. **Settings → Devices & Services → + Add Integration** → search "Dreame" → enter your Dreamehome app credentials

### Manual Installation

1. Download or clone this repo
2. Copy `custom_components/dreame_airpurifier/` into your HA `config/custom_components/` directory
3. Restart Home Assistant
4. **Settings → Devices & Services → + Add Integration** → search "Dreame"

## Setup

- Use your **Dreamehome app** credentials (email + password)
- Select your server region (US, EU, CN, etc.)
- The integration automatically discovers all FP10 purifiers on your account
- Multiple purifiers are supported — each appears as a separate device in HA

## Important Notes

### Cloud Polling
This integration communicates via the Dreame Cloud API (same as the Dreamehome app). It polls for state updates every x seconds (configurable, default is 30). Commands are sent through the cloud — there is no local API available for this device.

## Verified Property Map

For anyone looking to extend this integration or build their own, here's the complete MiOT property that I discovered via manual api calls:

| siid | piid | Property | Values |Notes|
|------|------|----------|--------|-----|
| 2 | 1 | Power | 1=on, 2=standby | read-only|
| 2 | 3 | Mode | 0=Auto, 2=Sleep, 3=Custom, 4=Pet |
| 2 | 4 | Fan Speed | 1-10 | works in custom mode |
| 3 | 2 | Humidity | 0-100% | 
| 3 | 3 | Temperature | C/K | unit is configurable |
| 3 | 4 | AQ | 1-4 | 1 - excellent, 2 - good, 3 = moderate pollution, 4 - poor |
| 3 | 5 | PM2.5 | µg/m³ |
| 3 | 6 | TVOC | µg/m³ |
| 4 | 1 | Filter Life | 0-100% |
| 4 | 2 | Filter Lifespan | Total days |
| 4 | 3 | Filter Used | 0-1 |
| 4 | 5 | Hair Collection Box Life | 0-100% | % remaining until cleaning |
| 4 | 6 | Hair Collection Box Lifespan | Total days | days until cleaning |
| 6 | 1 | Timezone | String | ex. "Europe/Warsaw" |
| 6 | 3 | Device Location | String | ex. "Łódź/Voivodeship,Łódź" |
| 6 | 4 | Temperature unit | 0=C, 1=F |
| 6 | 6 | Light Brightness Settings | 0=off, 1=on (last value), 30=dim, 50=natural, 80=bright |
| 6 | 8 | Timer | 0-12 | hours to automatic turn off |
| 6 | 10 | Child Lock | 0=off, 1=on |
| 6 | 11 | Weigth unit | 0=kg, 1=lb |
| 6 | 12 | Breating Light Mode | 0=off, 1=on |
| 6 | 17 | Key Tone Settings | 0=off, 1=on |
| 7 | 1 | Filter Self-Cleaning Status | 0=off, 1=in progress, 2=finished | (read-only) 2 is the status which waits until you manually dispose hair from the box and confirm with toggle action (`siid:7, aiid:2`), then it goes back to 0

Some settings cannot be changed by set_properties call. They require toggle action which uses a.o. siid and aiid. 

| siid | aiid | params | Function | Notes |
|------|------|--------|----------|-------|
| 2 | 1 |[{"piid": 1, "value": true}] | power on/off (standby/running) | true - running, false - standby |
| 2 | 3 | | factory reset | resets device to factory settings |
| 4 | 1 | | resets filter life | im not sure which one |
| 4 | 3 | | unknown | is accepted, but effect is not known |
| 5 | 1 | | unknown | is accepted, but effect is not known |
| 5 | 2 | | unknown | is accepted, but effect is not known |
| 7 | 1 | | start self cleaning procedure | starts the roller for 80 sec cleaning |
| 7 | 2 | | confirms self cleaning finished | should be called after hair box is manually cleaned after roller stopped cleaning |


## Troubleshooting

- **Login fails?** Verify your credentials work in the Dreamehome app. The integration uses the same login.
- **Device unavailable?** Make sure the purifier is powered on (not in deep standby). Check that it shows online in the Dreamehome app.
- **Commands not working?** Check HA logs under Developer Tools → Logs, search for `dreame_airpurifier`.
- **State not updating?** The integration polls every 30 seconds. Cloud state can sometimes lag behind physical changes.

## Contributing

Issues, feature requests, and PRs welcome.

## License

MIT License
