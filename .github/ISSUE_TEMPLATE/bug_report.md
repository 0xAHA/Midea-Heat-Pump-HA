---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

---
name: 🐛 Bug Report
about: Report a bug or unexpected behavior
title: '[BUG] '
labels: 'bug, needs-triage'
assignees: ''
---

## Pre-submission Checklist
<!-- Please confirm you have completed these steps -->
- [ ] I have searched existing issues for this problem
- [ ] I have tried the latest version of the integration
- [ ] I have checked the troubleshooting guide in the README

## 🐛 Bug Description
<!-- A clear and concise description of what the bug is -->

## 🔄 Steps to Reproduce
1. Go to Settings > Devices & Services
2. Configure integration with these settings...
3. Try to set temperature to 65°C
4. See error

## ✅ Expected Behavior
<!-- What should have happened? -->

## ❌ Actual Behavior
<!-- What actually happened? -->

## 📦 Environment Information

**Integration Version:** 
- [ ] v0.2.3 (latest)
- [ ] v0.2.2
- [ ] v0.2.1
- [ ] v0.2.0
- [ ] v0.1.x or earlier
- [ ] Custom/development branch

**Home Assistant Version:** (e.g., 2025.9.1)

**Setup Method:**
- [ ] Profile-based setup (loaded existing profile)
- [ ] Manual configuration  
- [ ] Updated from earlier version
- [ ] Other: ___________

## 🔥 Heat Pump Information
```
Brand: Midea/Chromagen/etc.
Model: HP170, HP280, etc.
Capacity: 170L, 280L, etc.
Year/Age: 2022, ~3 years old, etc.
Modbus Adapter: USR-TCP232-T2, Waveshare, etc.
```

## 🛠️ Configuration Details
<!-- Your integration configuration (remove IP addresses!) -->
```
Host: 192.168.1.XXX
Port: 502
Target temp register: 2
Target temp scale: 1
Target temp offset: 0
Current temp register: 102
Current temp scale: 0.5
Current temp offset: -15
# etc...
```

## 📋 Error Messages/Logs
<!-- Copy any relevant error messages from the HA logs -->
```
Logger: custom_components.midea_heatpump_hws.coordinator
ExceptionResponse(dev_id=1, function_code=134, exception_code=3)
```

## 🧪 Testing Done
<!-- Mark what you've already tried -->
- [ ] Restarted Home Assistant
- [ ] Checked network connectivity to heat pump
- [ ] Tested with manual Modbus tools
- [ ] Tried different configuration settings
- [ ] Checked for duplicate integrations

## 📝 Additional Context
<!-- Add any other context about the problem here -->
- Screenshots of the error
- What was happening before the bug occurred  
- Any recent changes to your setup
- Results from manual Modbus testing (if applicable)
