"""Config flow for OpenWeatherMap."""
from pyowm import OWM
from pyowm.utils.config import get_default_config
from pyowm.commons.exceptions import APIRequestError, UnauthorizedError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MODE,
    CONF_NAME,
    CONF_URL,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_LANGUAGE,
    CONFIG_FLOW_VERSION,
    DEFAULT_FORECAST_MODE,
    DEFAULT_LANGUAGE,
    DEFAULT_NAME,
    DEFAULT_URL,
    DEFAULT_USE_SSL,
    DEFAULT_VERIFY_SSL_CERTS,
    DEFAULT_USE_PROXY,
    DEFAULT_HAS_SUBDOMAINS,
    DEFAULT_HAS_PATH,
    DOMAIN,
    FORECAST_MODES,
    LANGUAGES,
)

class OpenWeatherMapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for OpenWeatherMap."""

    VERSION = CONFIG_FLOW_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OpenWeatherMapOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            latitude = user_input[CONF_LATITUDE]
            longitude = user_input[CONF_LONGITUDE]
            url = user_input[CONF_URL]

            await self.async_set_unique_id(f"{latitude}-{longitude}")
            self._abort_if_unique_id_configured()

            try:
                api_online = await _is_owm_api_online(
                    self.hass, user_input[CONF_API_KEY], latitude, longitude, url
                )
                if not api_online:
                    errors["base"] = "invalid_api_key"
            except UnauthorizedError:
                errors["base"] = "invalid_api_key"
            except APIRequestError:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Optional(
                    CONF_LATITUDE, default=self.hass.config.latitude
                ): cv.latitude,
                vol.Optional(
                    CONF_LONGITUDE, default=self.hass.config.longitude
                ): cv.longitude,
                vol.Optional(CONF_MODE, default=DEFAULT_FORECAST_MODE): vol.In(
                    FORECAST_MODES
                ),
                vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(
                    LANGUAGES
                ),
                vol.Optional(CONF_URL, default=DEFAULT_URL): cv.string,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class OpenWeatherMapOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
        )

    def _get_options_schema(self):
        return vol.Schema(
            {
                vol.Optional(
                    CONF_MODE,
                    default=self.config_entry.options.get(
                        CONF_MODE, DEFAULT_FORECAST_MODE
                    ),
                ): vol.In(FORECAST_MODES),
                vol.Optional(
                    CONF_LANGUAGE,
                    default=self.config_entry.options.get(
                        CONF_LANGUAGE, DEFAULT_LANGUAGE
                    ),
                ): vol.In(LANGUAGES),
                vol.Optional(
                    CONF_URL,
                    default=self.config_entry.options.get(
                        CONF_URL, DEFAULT_URL
                    ),
                ): cv.string, 
            }
        )

async def _is_owm_api_online(hass, api_key, lat, lon, url):

    config_dict = _get_owm_config(CONF_LANGUAGE, url)
    owm = OWM(api_key, config_dict).weather_manager()

    return await hass.async_add_executor_job(owm.one_call, lat, lon)

def _get_owm_config(language, url):
    """Get OpenWeatherMap configuration and add language to it."""
    config_dict = get_default_config()
    config_dict["language"] = language
    config_dict["url"] = url
    config_dict['connection']['has_subdomains'] = DEFAULT_HAS_SUBDOMAINS
    config_dict['connection']['has_path'] = DEFAULT_HAS_PATH
    config_dict['connection']['use_ssl'] = DEFAULT_USE_SSL
    config_dict['connection']['verify_ssl_certs'] = DEFAULT_VERIFY_SSL_CERTS
    config_dict['connection']['use_proxy'] = DEFAULT_USE_PROXY
    return config_dict    
