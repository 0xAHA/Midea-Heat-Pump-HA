# 🤝 Contributing to Midea Heat Pump HA Integration

*Because great integrations are built by great communities!*

Welcome to the contributor's guide! Whether you're fixing bugs, adding features, or sharing device profiles, we're thrilled to have you aboard.

## 🎯 Ways to Contribute

### 📋 **Share Your Device Profile** (The Easy Win!)
Got a working configuration for a different model? This is the most valuable contribution you can make!

1. **Export your profile**:
   ```yaml
   service: midea_heatpump_hws.export_profile
   data:
     name: "My Working 280L Config"
     model: "HP280-XYZ"
   ```

2. **Submit via GitHub issue** using our [Device Profile template](.github/ISSUE_TEMPLATE/hws-device-profile-submission.md)

### 🐛 **Report Issues**
Found a bug? Use our issue templates to help us understand and fix it quickly:
- [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) - For when something's not working
- [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) - For new functionality ideas

### 📚 **Improve Documentation**
Spotted a typo? Missing info? Documentation PRs are always welcome!

---

## 🐛 Reporting Issues

**Before submitting**: Search existing issues - someone might have already reported it! 

**Use the right template**: We have specific issue templates to help gather the information we need:
- **[Bug Report](.github/ISSUE_TEMPLATE/bug_report.md)** - Something's broken
- **[Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)** - You have a great idea  
- **[Device Profile](.github/ISSUE_TEMPLATE/hws-device-profile-submission.md)** - Share your working config

The templates ensure you include all the details we need to help you quickly!

---

## 🚀 Development Guidelines

### Getting Started

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/yourusername/Midea-Heat-Pump-HA.git
   cd Midea-Heat-Pump-HA
   ```
3. **Create a branch**:
   ```bash
   git checkout -b feature/awesome-new-feature
   # or
   git checkout -b fix/temperature-bug
   ```

### Development Setup

#### **Home Assistant Dev Environment**
```bash
# Set up HA dev environment (if testing locally)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install homeassistant
```

#### **Testing Your Changes**
1. **Copy to HA config**:
   ```bash
   cp -r custom_components/midea_heatpump_hws /path/to/homeassistant/config/custom_components/
   ```
2. **Restart Home Assistant**
3. **Test thoroughly** with your actual hardware (if possible)
4. **Check logs** for any errors or warnings

### Code Standards

#### **Python Style**
- **Follow Home Assistant standards** - check existing integration code for patterns
- **Use type hints** where possible
- **Keep functions focused** - one responsibility per function
- **Add docstrings** for public methods
- **Handle exceptions gracefully** - don't let Modbus errors crash HA

#### **Example Good Code**
```python
async def async_set_temperature(self, **kwargs: Any) -> None:
    """Set target temperature with proper validation and error handling."""
    temperature = kwargs.get(ATTR_TEMPERATURE)
    
    if temperature is None:
        _LOGGER.warning("No temperature provided")
        return
        
    # Validate against mode-specific limits
    if not self._is_temperature_valid(temperature):
        _LOGGER.error(
            "Temperature %s°C outside valid range for mode %s", 
            temperature, self.current_operation
        )
        return
        
    try:
        scaled_temp = self._scale_target_temperature(temperature)
        await self.coordinator.async_write_register(
            self._target_temp_register, 
            scaled_temp
        )
        _LOGGER.debug("Successfully set temperature to %s°C", temperature)
    except Exception as err:
        _LOGGER.error("Failed to set temperature: %s", err)
        raise HomeAssistantError(f"Cannot set temperature: {err}") from err
```

### Commit Guidelines

#### **Commit Messages**
Use conventional commits format:
- `feat:` - new feature
- `fix:` - bug fix  
- `docs:` - documentation changes
- `refactor:` - code refactoring
- `test:` - adding tests
- `profile:` - adding/updating device profiles

**Examples:**
```
feat: add support for 300L models with different register layout
fix: temperature scaling error when target temp offset is non-zero  
profile: add Chromagen HP280 configuration
docs: update troubleshooting guide with common Modbus errors
```

#### **What Makes a Good PR**

✅ **DO:**
- **Test on real hardware** (if you have it)
- **Update documentation** if you change functionality  
- **Add profiles** to the defaults folder if supporting new models
- **Keep changes focused** - one feature/fix per PR
- **Add meaningful commit messages**
- **Include screenshots** for UI changes

❌ **DON'T:**
- Mix multiple unrelated changes
- Break existing functionality  
- Remove error handling
- Skip testing (we know hardware testing is hard, but try!)

### Pull Request Process

1. **Create your PR** - our [PR template](.github/pull_request_template.md) will guide you
2. **Ensure CI passes** (when we add automated tests)
3. **Respond to review feedback** - we're here to help make your contribution great!
4. **Celebrate** when it's merged! 🎉

---

## 📚 External Resources

### **Home Assistant Development**
- [HA Developer Docs](https://developers.home-assistant.io/) - Official development guide
- [Integration Development](https://developers.home-assistant.io/docs/creating_integration_index) - Step-by-step integration guide  
- [Config Flow Best Practices](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/) - UI configuration patterns

### **Modbus & Hardware**  
- [pymodbus Documentation](https://pymodbus.readthedocs.io/) - Python Modbus library
- [Modbus Protocol Guide](https://www.modbustools.com/modbus.html) - Understanding Modbus basics
- [RS485 to WiFi Adapters](https://community.home-assistant.io/t/chromagen-midea-170l-heat-pump-hot-water-system-modbus-integration-success/773718/12) - Hardware setup discussion

### **Project References**
- [Original HA Community Thread](https://community.home-assistant.io/t/chromagen-midea-170l-heat-pump-hot-water-system-modbus-integration-success/773718/12) - Where it all started
- [BrittonA's Original Config](https://gist.github.com/BrittonA/339d25efb934bdb4f451ba7e2f920ba3) - Initial YAML implementation

---

## 🎯 Community Guidelines

### **Our Values**

**🤝 Be Helpful** - Everyone started somewhere. If someone's struggling with Modbus registers, help them out rather than saying "RTFM"

**🔧 Share Knowledge** - Got a working config? Share it! Found a fix? Document it! Your solution might save someone hours of debugging

**🧪 Test Thoroughly** - Heat pump integrations control real hardware. A bug isn't just annoying, it could affect someone's hot water supply

**📖 Document Everything** - Future you (and others) will thank present you for clear documentation

### **Communication Style**

- **Be patient** - Modbus can be frustrating, especially for newcomers
- **Be specific** - "It doesn't work" vs "Temperature shows 15°C instead of actual 55°C"  
- **Be constructive** - Instead of "This is wrong", try "Here's what I found works better"
- **Celebrate wins** - Someone got their 300L model working? That's awesome! 🎉

### **Code of Conduct**

We follow the [Home Assistant Code of Conduct](https://github.com/home-assistant/core/blob/dev/CODE_OF_CONDUCT.md). 

**TL;DR**: Be excellent to each other. We're all here because we love Home Assistant and want reliable hot water! ♨️

---

## 🏆 Recognition

### **Hall of Fame** ⭐

Contributors who've made significant impacts:

- **dgomes** - Original generic water heater foundation
- **ill_hey** - Hardware reverse engineering pioneer  
- **BrittonA** - First working Modbus configuration
- **[Your name here?]** - Next great contributor!

### **Profile Contributors** 📋

When you submit a working profile, we'll add you to the credits in:
- The profile file itself
- Release notes  
- README acknowledgments

---

## 🆘 Getting Help

### **Stuck on Development?**
- **GitHub Discussions** - Ask questions, discuss ideas
- **Issues** - For specific bugs or feature requests
- **HA Community Forum** - [Original thread](https://community.home-assistant.io/t/chromagen-midea-170l-heat-pump-hot-water-system-modbus-integration-success/773718/12) still active

### **Need Hardware Help?**
The integration is only as good as the hardware setup. If you're struggling with:
- RS485 to WiFi adapters
- Finding the right Modbus registers
- Understanding your heat pump's communication protocol

Don't hesitate to ask! The community has collective experience with dozens of different setups.

---

## 🎉 Final Words

Every contribution matters - whether it's a typo fix, a new device profile, or a major feature. The goal is simple: make reliable hot water automation accessible to everyone.

Ready to contribute? We can't wait to see what you build! 

*Happy coding! 🚀*

---

*Questions about these guidelines? Open an issue with the label `question` and we'll help clarify!*
