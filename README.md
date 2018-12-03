# Home Assistant Home Connect

This is work in progress of an implementation of a Home Connect component for Home Assistant.

## Usage

- Register an account with the [Home Connect Developer Program](https://developer.home-connect.com)
- Register a new application with the Redirect URI `https://YOUR_HOMEASSISTANT_BASE_URL:PORT/api/homeconnect` (it will not work without https)
- Copy the contents of `custom_components` to the  `custom_components` directory of your Home Assistant configuration directory
- Add the following to your `configuration.yaml`:
```yaml
homeconnect:
  client_id: YOUR_CLIENT_ID
  client_secret: YOUR_CLIENT_SECRET
```

## Feedback

This is an early development preview (**use at your own risk!**). Please report problems by [opening an issue](https://github.com/DavidMStraub/homeassistant-homeconnect/issues).

Pull requests are welcome!
