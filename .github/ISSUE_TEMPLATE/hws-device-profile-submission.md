---
name: HWS Device Profile Submission
about: Describe this issue template's purpose here.
title: ''
labels: ''
assignees: ''

---

---
name: 📋 Device Profile Submission
about: Share your working heat pump configuration
title: '[PROFILE] '
labels: 'profile, device-support'
assignees: ''
---

🎉 **Thank you for sharing your working configuration!** 

Device profiles help other users with the same model get up and running quickly. 
Your contribution could save someone hours of register hunting!

## 🔥 Heat Pump Details
**Brand:** (Chromagen, original manufacturer if rebrand)  
**Model:** (HP280-ABC123)  
**Capacity:** (280L)  
**Year/Age:** (2022 / ~3 years old)  
**Region:** (Australia, US, EU, etc.)  
**Purchase Location:** (Bunnings, Home Depot, local installer, etc.)  
**Model Variations:** (Different control panel, firmware version, etc.)  

## 🔌 Hardware Setup
**Modbus Adapter:** (USR-TCP232-T2)  
**Connection Type:** (RS485 to WiFi)  
**Network Connection:** (Wired/WiFi to home network)  
**Physical Wiring:** (Wired to control board terminals X, Y)  
**Special Notes:** (Polarity matters, used specific terminals, etc.)  

## ✅ Testing Completed
<!-- Confirm your configuration is fully working -->
- [ ] Can read all temperature sensors correctly
- [ ] Can successfully change operation modes (Eco, Performance, Electric)
- [ ] Can set target temperature within valid ranges
- [ ] Integration stays connected (no frequent 'unavailable' states)
- [ ] Tested for at least 24 hours without issues

## 📊 Register Configuration
**Control Registers:**
- Power register: 
- Mode register: 
- Target temperature register: 

**Temperature Registers:**
- Current temp register: 
- Tank top register: 
- Tank bottom register: 
- Outdoor temp register: 
- Condensor temp register: 
- Other sensors: 

**Scaling Values:**
- Current temp: offset=___, scale=___
- Target temp: offset=___, scale=___
- Other sensors: offset=___, scale=___

**Operation Mode Values:**
- Eco mode: 
- Performance mode: 
- Electric mode: 

## 🌡️ Temperature Limits
**Eco Mode:** ___°C - ___°C  
**Performance Mode:** ___°C - ___°C  
**Electric Mode:** ___°C - ___°C  

**Temperature Limit Notes:**
(e.g., Going above 60°C in Eco mode causes Modbus error, Unit physically limits to 75°C)

## 📄 Exported Profile
<!-- Use the service call to export your profile -->
```yaml
# Use this service call to export:
service: midea_heatpump_hws.export_profile
data:
  name: "HP280 Working Config"
  model: "HP280-ABC123"
```

<!-- Then paste the JSON content here or attach the downloaded file -->
```json
{
  "paste your exported profile here"
}
```

## 📝 Quirks & Special Notes
**Setup Challenges:**
- Had to use different register than expected
- Required specific Modbus settings
- Wiring was different than documentation

**Operational Notes:**
- Takes 30 seconds for temperature changes to show
- Mode switching sometimes requires 2 attempts
- Some sensors only work in certain modes

**Compared to other models:**
- Uses register 5 instead of 2 for target temp
- Different temperature scaling than 170L model

## 📤 Profile Sharing Permission
<!-- Can we include this profile in future releases? -->
- [ ] Yes - include in built-in profiles for others to use
- [ ] Yes - but credit me as contributor
- [ ] No - just for troubleshooting this issue

## 🤝 Additional Help Offered
<!-- How else might you be able to help other users with this model? -->
- [ ] Happy to help troubleshoot others with same model
- [ ] Can provide photos of my setup/wiring
- [ ] Available for testing new features  
- [ ] Can help document setup process

---
**What happens next:**
1. We'll review your profile and test it (if possible)
2. If everything looks good, we'll include it in the next release
3. You'll be credited as a contributor in the release notes
4. Other users will benefit from your work - thank you! 🙏
