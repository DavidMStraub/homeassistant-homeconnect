**:warning: Breaking change: as of version 1.0, the component has been renamed and this repository will be used for beta testing new features that are not part of the Home Assistant Core Home Connect integration based on this work. :warning:**

# Home Assistant Home Connect development repository

Custom component for testing experimental features of the Home Assistant Home Connect intgegration.


## Usage

1. Register an account with the [Home Connect Developer Program](https://developer.home-connect.com)
2. [Register a new application](https://developer.home-connect.com/applications/add) with `OAuth Flow` type `Authorization Code Grant Flow` and Redirect URI `https://YOUR_HOMEASSISTANT_BASE_URL:PORT/auth/external/callback` (it will not work without https, but your Home Assistant instance does *not* have to be accessible from the internet and a self-signed certificate will do)
3. Make sure the `http` component in your `configuration.yaml` has the base url set to `YOUR_HOMEASSISTANT_BASE_URL:PORT` (it will not work otherwise)
4. Add the following to your `configuration.yaml`:
```yaml
home_connect_beta:
  client_id: YOUR_CLIENT_ID
  client_secret: YOUR_CLIENT_SECRET
```
5. Copy the contents of `custom_components` to the  `custom_components` directory of your Home Assistant configuration directory
6. Navigate to the Integrations page and select "Home Connect"

Step 5 can also be replaced by using [HACS](https://hacs.xyz/) and adding this repository as a custom repistory.

## Feedback

Since the Home Connect component originally developed in this repository has been [merged](https://github.com/home-assistant/home-assistant/pull/29214) into Home Assistant Core as of May 5, 2020, this custom component will only be used for testing new features. You are welcome to contribute pull requests, but of course any bug fixes and serious improvements can also be directly submitted to Home Assistant Core.
