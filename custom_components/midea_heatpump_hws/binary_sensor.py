"""Binary sensors for Midea Heat Pump diagnostic state registers."""
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_MODBUS_UNIT,
    CONF_HEATER_ASSIST_REGISTER,
    CONF_SANITIZE_STATE_REGISTER,
)
from .coordinator import MideaModbusCoordinator

_LOGGER = logging.getLogger(__name__)

# Register 109 values that indicate an active sanitize cycle
_SANITIZE_ACTIVE_VALUES = {32, 33}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Midea diagnostic binary sensors from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    config = hass.data[DOMAIN][config_entry.entry_id]["config"]

    host_suffix = f" ({config['host']})"
    entities = []

    if config.get(CONF_HEATER_ASSIST_REGISTER) is not None:
        entities.append(
            MideaBinarySensor(
                coordinator=coordinator,
                config=config,
                data_key="heater_assist_raw",
                name=f"Heater Assist{host_suffix}",
                register=config[CONF_HEATER_ASSIST_REGISTER],
                device_class=BinarySensorDeviceClass.RUNNING,
                is_on_fn=lambda v: v != 0,
            )
        )

    if config.get(CONF_SANITIZE_STATE_REGISTER) is not None:
        entities.append(
            MideaBinarySensor(
                coordinator=coordinator,
                config=config,
                data_key="sanitize_state_raw",
                name=f"Sanitize Cycle Active{host_suffix}",
                register=config[CONF_SANITIZE_STATE_REGISTER],
                device_class=BinarySensorDeviceClass.RUNNING,
                is_on_fn=lambda v: v in _SANITIZE_ACTIVE_VALUES,
            )
        )

    async_add_entities(entities)


class MideaBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Read-only binary sensor derived from a raw diagnostic register value."""

    def __init__(
        self,
        coordinator: MideaModbusCoordinator,
        config: dict,
        data_key: str,
        name: str,
        register: int,
        device_class: BinarySensorDeviceClass,
        is_on_fn,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._config = config
        self._data_key = data_key
        self._register = register
        self._is_on_fn = is_on_fn

        self._attr_name = name
        self._attr_unique_id = f"midea_{config['host']}_{config[CONF_MODBUS_UNIT]}_{data_key}"
        self._attr_device_class = device_class

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info to group this sensor with the main device."""
        return {
            "identifiers": {(DOMAIN, f"{self._config['host']}_{self._config[CONF_MODBUS_UNIT]}")},
            "name": f"Midea Heat Pump ({self._config['host']})",
            "manufacturer": "Midea",
            "model": "Heat Pump Water Heater",
        }

    @property
    def is_on(self) -> bool | None:
        """Return True when the register value indicates active state."""
        raw = (self.coordinator.data or {}).get(self._data_key)
        if raw is None:
            return None
        return self._is_on_fn(raw)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._data_key in (self.coordinator.data or {})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator, logging raw register value."""
        raw = (self.coordinator.data or {}).get(self._data_key)
        _LOGGER.debug(
            "%s: register %s raw=%s -> is_on=%s",
            self._attr_name,
            self._register,
            raw,
            self._is_on_fn(raw) if raw is not None else None,
        )
        self.async_write_ha_state()
