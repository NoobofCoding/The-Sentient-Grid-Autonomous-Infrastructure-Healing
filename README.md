# The-Sentient-Grid-Autonomous-Infrastructure-Healing
Critical infrastructure (power grids, water systems) currently uses 'Passive Monitoring.' When a failure  occurs, humans must analyze the data and intervene. In a national emergency, this delay is fatal. The  challenge is to create a system where the grid 'thinks' and re-routes itself before a human even sees the  alert.

# ⚡ Sentient Grid: Autonomous Infrastructure Healing

> **Making power grids think faster than humans. Autonomous control + LLM explainability for real-time grid stabilization.**

[![Status](https://img.shields.io/badge/Status-Active%20Development-blue)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Stage](https://img.shields.io/badge/Stage-2%3A%20Digital%20Twin-yellow)]()

---

## 🚨 The Problem

**Current State: Passive Monitoring (2-5 minute response)**
```
Voltage Sag Detected → Alert to Operator → Operator Analyzes → Decision → Manual Command → Grid Stabilizes
          ↓                    ↓                     ↓              ↓             ↓
       <1 sec              30-45 sec              60 sec         90 sec       2-3 min
                                                                          ❌ TOO LATE
                                    By this time: 50,000 homes lost power
                                                  $2M+ in damages
                                                  Cascading blackout started
```

**Desired State: Autonomous Healing (<100 milliseconds)**
```
Voltage Sag Detected → Anomaly Detector → Autonomous Decision → Load Shedding → Grid Stabilizes
          ↓                   ↓                    ↓                  ↓              ↓
       <1 sec              50 ms               80 ms             <100 ms        2-4 sec
                                                                            ✅ CRISIS PREVENTED
```

### Why This Matters (Right Now, 2025)

- **Blackout Crisis:** Power outages up 150% since 2015. April 2025 Iberian Peninsula: 15 GW loss in 5 seconds across 4 countries
- **Renewable Volatility:** 40%+ of new generation is solar/wind (no inertia). One cloud = grid instability
- **Data Center Explosion:** AI infrastructure adding 15-20 GW new demand annually. Grid can't keep up manually
- **Human Bottleneck:** Operators drowning in data. Can't analyze 1M data points/second. Workforce aging out

**Result:** Grid is becoming *less stable* right when demand is *highest*

---

## 💡 The Solution: Sentient Grid

A **three-layer autonomous system** that detects faults, responds immediately, and explains every decision:

```
┌──────────────────────────────────────────────────────────────────┐
│                    LAYER 3: EXPLAINABILITY                        │
│  LLM generates natural language justification for every action   │
│  "At 2:32 PM, voltage sag detected. Shed 25 MW non-essential.   │
│   Recovery: 4 minutes. Prevented cascading blackout."            │
└──────────────────────────────────────────────────────────────────┘
                              ↑
┌──────────────────────────────────────────────────────────────────┐
│                    LAYER 2: AUTONOMOUS CONTROL                    │
│  RL Agent or Rule-Based System makes millisecond decisions       │
│  IF voltage < 90% THEN shed loads [3, 5, 7]                    │
│  Action execution: <100 ms                                       │
└──────────────────────────────────────────────────────────────────┘
                              ↑
┌──────────────────────────────────────────────────────────────────┐
│                  LAYER 1: REAL-TIME DETECTION                     │
│  Anomaly detector scores grid state continuously                │
│  Isolation Forest / LSTM catches voltage sags, freq deviations  │
│  Detection latency: <50 ms                                       │
└──────────────────────────────────────────────────────────────────┘
                              ↑
                      SCADA Data Stream
                     (IEEE-39 or Real Grid)
```

---

## 🏗 Architecture: 4 Pillars

This project is organized into **4 independent pillars** that work together:

### **Pillar 1: Grid Simulation & Digital Twin** 👈 *You Are Here*
- **Owns:** Power grid physics, state modeling, environment
- **Builds:** IEEE-39 bus system simulator
- **Delivers:** `GridEnvironment` (Gym-compatible)
- **Status:** 🟡 STAGE 2 (Digital Twin Core)
- **Lead:** Grid/Power Systems Engineer

### **Pillar 2: Reinforcement Learning Engine**
- **Owns:** RL training, policy learning, decision making
- **Uses:** GridEnvironment from Pillar 1
- **Delivers:** Trained PPO agent
- **Status:** 🔵 STAGE 3 (RL Agent Development)
- **Lead:** ML Engineer

### **Pillar 3: Safety & System Validation**
- **Owns:** Guardrails, safety filters, stress testing
- **Tests:** Stability metrics, edge cases, failure modes
- **Delivers:** Safe action wrapper
- **Status:** 🟣 STAGE 4 (Safety Layer)
- **Lead:** Control Systems Engineer

### **Pillar 4: Explainability → Dashboard → Visualization**
- **Phase A:** LLM reasoning (Featherless AI/Claude)
- **Phase B:** 2D monitoring dashboard (Streamlit/Flask)
- **Phase C:** 3D visualization (Three.js smart city)
- **Status:** 🟠 STAGE 5-8 (Multi-Phase)
- **Lead:** Full-Stack / ML Engineer

---

## 📊 Current Status: STAGE 2

```
🟢 STAGE 1: Problem Formalization & Control Design ✅ COMPLETE
   └─ Architecture defined, state/action/reward spaces clear

🟡 STAGE 2: Digital Twin Environment (ACTIVE) ⚙️ IN PROGRESS
   ├─ IEEE-39 bus model: 39 buses, 46 lines, 10 generators
   ├─ Power flow solver: Simplified AC power flow
   ├─ Gym wrapper: env.reset(), env.step(action)
   ├─ Fault injection: voltage_sag, line_outage, load_spike
   └─ Testing: Determinism, reproducibility checks

🔵 STAGE 3: RL Agent Development (QUEUED)
   └─ Starts once Pillar 1 is validated

🟣 STAGE 4: Safety & Guardrails (QUEUED)

🟠 STAGE 5: Explainability Layer (QUEUED)

🟤 STAGE 6: 2D Dashboard (QUEUED)

🔴 STAGE 7: Stress Testing (QUEUED)

🟣 STAGE 8: 3D Visualization (QUEUED)
```

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
pip, git
```

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/sentient-grid.git
cd sentient-grid

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage (Stage 2: Testing the Simulator)

```python
from pillar_1.grid_model import IEEE39BusGrid
from pillar_1.gym_grid_env import GridEnvironment

# Initialize environment
env = GridEnvironment()
obs = env.reset()

print(f"Initial observation shape: {obs.shape}")
print(f"Action space: {env.action_space}")

# Run 100 steps with random actions
for step in range(100):
    action = env.action_space.sample()  # Random load shedding
    obs, reward, done, info = env.step(action)
    
    print(f"Step {step}: V_min={info['voltage_min']:.3f}, "
          f"F={info['frequency']:.2f} Hz, "
          f"Stable={info['is_stable']}")
    
    if done:
        print(f"Episode ended at step {step}")
        break

# Test fault injection
env.reset()
env.inject_fault(fault_type='voltage_sag', location=10, severity=0.5)

for step in range(50):
    # Agent tries to stabilize grid
    action = np.zeros(21)
    action[[3, 5, 7]] = 0.8  # Shed loads 3, 5, 7
    obs, reward, done, info = env.step(action)

print(f"Recovery successful: {env.grid.is_stable()}")
```

---

## 📁 Project Structure

```
sentient-grid/
├── README.md                          # This file
├── requirements.txt                   # Dependencies
├── LICENSE                            # MIT
│
├── pillar_1_grid_simulation/          # 🏗 PILLAR 1: Digital Twin (Pillar 1 code)
│   ├── __init__.py
│   ├── grid_model.py                  # IEEE39BusGrid class
│   │   ├── IEEE39BusGrid (main class)
│   │   ├── _load_ieee39_buses()
│   │   ├── _load_ieee39_lines()
│   │   ├── _load_ieee39_generators()
│   │   ├── _load_ieee39_loads()
│   │   ├── inject_fault()
│   │   ├── apply_load_shed()
│   │   ├── step(dt)
│   │   ├── _solve_power_flow()
│   │   ├── is_stable()
│   │   └── _get_state()
│   │
│   ├── gym_grid_env.py                # GridEnvironment(gym.Env)
│   │   ├── GridEnvironment class
│   │   ├── reset()
│   │   ├── step(action)
│   │   ├── _calculate_reward()
│   │   ├── _normalize_state()
│   │   ├── inject_fault()
│   │   └── render()
│   │
│   ├── tests/
│   │   ├── test_stage2_basic.py       # Basic environment tests
│   │   ├── test_fault_injection.py    # Fault scenarios
│   │   ├── test_determinism.py        # Reproducibility checks
│   │   └── test_stability_metrics.py  # Stability validation
│   │
│   └── data/
│       ├── case39.m                   # MATPOWER IEEE-39 case
│       └── ieee39_bus_data.npy        # Preprocessed grid data
│
├── pillar_2_rl_agent/                 # 🤖 PILLAR 2: RL Engine (TODO)
│   ├── train.py
│   ├── agent.py
│   └── models/
│
├── pillar_3_safety_validation/        # 🛡 PILLAR 3: Safety Layer (TODO)
│   ├── guardrails.py
│   ├── stress_tests.py
│   └── metrics.py
│
├── pillar_4_explainability/           # 🧠 PILLAR 4: LLM + Dashboard (TODO)
│   ├── llm_engine.py
│   ├── dashboard.py
│   └── visualization.py
│
└── docs/
    ├── ARCHITECTURE.md                # Full system design
    ├── PILLAR_1_DETAILS.md            # Grid model spec
    ├── API.md                         # GridEnvironment API
    ├── STAGE_ROADMAP.md               # 8-stage development plan
    └── CONTRIBUTING.md                # How to contribute
```

---

## 📚 Key Concepts

### **State Space**
Grid state is represented as a 154-dimensional vector:
- **39 Bus Voltages** (V1, V2, ..., V39)
- **39 Bus Angles** (θ1, θ2, ..., θ39)
- **10 Generator Speeds** (ω_gen1, ..., ω_gen10)
- **21 Load Demands** (P_load1, ..., P_load21)
- **5 Fault Flags** (fault_active, location, type, frequency, etc.)

### **Action Space**
Control is 21-dimensional (one per controllable load):
```
action = [a1, a2, ..., a21] where each ai ∈ [0, 1]
- 0 = no load shedding
- 1 = 100% load disconnection
Example: [0, 0.8, 0, 0.6, ...] = shed 80% of load 2, 60% of load 4
```

### **Reward Function**
```
reward = V_stability + F_stability + L_cost + bonus

V_stability = -10 * mean((V - 1.0)^2)      # Penalize voltage deviation
F_stability = -5 * (frequency - 60)^2      # Penalize frequency deviation
L_cost = -0.5 * sum(actions)                # Penalize load shedding
bonus = +1.0 if grid is stable              # Reward stability

Hard penalties:
- V < 0.8 or V > 1.2: -50 (safety violation)
- F < 59.0 or F > 61.0: -50 (safety violation)
```

### **Fault Types**
```python
env.inject_fault(
    fault_type='voltage_sag',      # 'voltage_sag' | 'line_outage' | 'load_spike'
    location=10,                    # Bus/line ID (0-38 for buses)
    severity=0.5                    # 0-1 scale (how severe)
)
```

---

## 🔬 Testing (Current Stage)

Run all Pillar 1 tests:
```bash
cd pillar_1_grid_simulation
python -m pytest tests/ -v
```

Specific tests:
```bash
# Basic environment sanity checks
python tests/test_stage2_basic.py

# Fault injection scenarios
python tests/test_fault_injection.py

# Ensure determinism (critical for RL)
python tests/test_determinism.py

# Validate stability metrics
python tests/test_stability_metrics.py
```

Expected output:
```
test_stage2_basic.py::test_reset ✓
test_stage2_basic.py::test_step ✓
test_stage2_basic.py::test_action_shape ✓
test_fault_injection.py::test_voltage_sag ✓
test_fault_injection.py::test_load_spike ✓
test_determinism.py::test_reproducibility ✓
test_stability_metrics.py::test_is_stable ✓

All tests passed! ✅
```

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Full system design + Pillar integration |
| [PILLAR_1_DETAILS.md](docs/PILLAR_1_DETAILS.md) | Grid model specifications |
| [API.md](docs/API.md) | GridEnvironment API reference |
| [STAGE_ROADMAP.md](docs/STAGE_ROADMAP.md) | 8-stage development plan |
| [CONTRIBUTING.md](docs/CONTRIBUTING.md) | How to contribute |

---

## 🎯 Roadmap

### **Current: STAGE 2 (Weeks 1-3)**
- [x] Problem formalization
- [x] IEEE-39 grid model design
- [ ] Power flow solver (AC simplified)
- [ ] Gym environment wrapper
- [ ] Fault injection testing
- [ ] Documentation

### **Next: STAGE 3 (Weeks 4-6)**
- [ ] RL agent integration (Stable Baselines3)
- [ ] PPO training
- [ ] Policy evaluation
- [ ] Benchmark against baseline

### **Future: STAGES 4-8 (Weeks 7-15)**
- [ ] Safety guardrails
- [ ] LLM explainability
- [ ] Monitoring dashboard
- [ ] Stress testing
- [ ] 3D visualization
- [ ] Live demo

---

## 🤝 Contributing

We're in **active development** and looking for contributors!

### How to Help

**Pillar 1 (Grid Simulation):**
- Improve power flow solver accuracy
- Add more fault types (transient stability, reactive power)
- Validate against real SCADA data
- Optimize computation speed

**Pillar 2 (RL Agent):**
- Experiment with different RL algorithms (SAC, TD3)
- Hyperparameter tuning
- Reward function refinement
- Training optimization

**Pillar 3 (Safety):**
- Design safety constraints
- Stress test scenarios
- Stability metrics
- Edge case handling

**Pillar 4 (Explainability):**
- LLM integration (Claude, Featherless AI)
- Dashboard frontend (Streamlit/Flask)
- Visualization engine (Three.js)
- Audit trail logging

### Getting Started
1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Make changes and test thoroughly
4. Submit PR with detailed description
5. See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines

---

## 📊 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| **Anomaly Detection Latency** | <50 ms | TBD (Stage 3) |
| **Autonomous Response Time** | <100 ms | TBD (Stage 3) |
| **Grid Stability Success Rate** | >95% | TBD (Stage 3) |
| **LLM Explanation Quality** | Understandable by operators | TBD (Stage 5) |
| **Simulation Determinism** | 100% reproducible | TBD (Stage 2 testing) |

---

## 🔗 Data Sources & References

### IEEE-39 Test Case
- [MATPOWER Case 39](https://github.com/MATPOWER/matpower/blob/master/data/case39.m)
- 39 buses, 46 lines, 10 generators
- New England test system (standard for grid research)

### Papers & Resources
- [NERC 2024 Grid Reliability Report](https://www.nerc.net/)
- [IEEE Standard for Synchrophasor Data](https://ieeexplore.ieee.org/)
- [Stable Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)

---

## 📜 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

---

## 👥 Team

| Pillar | Role | Status |
|--------|------|--------|
| **1** | Grid Simulation & Digital Twin | 🏗 Active |
| **2** | RL Agent Development | 🔵 Queued |
| **3** | Safety & Validation | 🛡 Queued |
| **4** | Explainability & Dashboard | 🧠 Queued |

---

## 💬 Questions? Need Help?

- **Issues:** Use GitHub Issues for bugs and feature requests
- **Discussions:** Start a GitHub Discussion for design questions
- **Email:** contact@sentientgrid.dev (placeholder)
- **Docs:** Check [docs/](docs/) folder for detailed guides

---

## 🌍 Real-World Impact

### Why This Matters

Between 2024 and 2028, 300 million people across the United States could face power outages due to demand growth and extreme weather. Summer peak demand is forecast to grow by 122 GW in the next decade, adding 15.7% to current peaks.

**Without autonomous grid control:**
- Cascading blackouts affect entire regions
- Recovery takes hours/days
- Economic losses: $130B+ per major event

**With Sentient Grid:**
- Faults detected in <50 milliseconds
- Response in <100 milliseconds
- Recovery in 2-4 seconds
- Cascading failures prevented

---

## 🎓 Learning Resources

### For Grid/Power Systems:
- "Power System Dynamics and Stability" - Peter Sauer & M.A. Pai
- MATPOWER documentation
- IEEE standards (synchrophasor data, protection)

### For RL:
- Stable Baselines3 tutorials
- "Reinforcement Learning: An Introduction" - Sutton & Barto

### For LLMs:
- Claude API documentation
- Prompt engineering best practices

---

## 📈 Citation

If you use Sentient Grid in your research, please cite:

```bibtex
@software{sentient_grid_2025,
  title={Sentient Grid: Autonomous Infrastructure Healing},
  author={Your Team},
  year={2025},
  url={https://github.com/yourusername/sentient-grid}
}
```

---

## ⚡ Quick Commands Cheat Sheet

```bash
# Setup
git clone https://github.com/yourusername/sentient-grid.git
cd sentient-grid
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests (current stage)
pytest pillar_1_grid_simulation/tests/ -v

# Run basic simulation
python -c "from pillar_1.gym_grid_env import GridEnvironment; env = GridEnvironment(); env.reset(); print('✅ Environment initialized')"

# View logs
tail -f logs/grid_simulation.log

# Contribute
git checkout -b feature/my-feature
# ... make changes ...
git commit -m "Feature: description"
git push origin feature/my-feature
# Open PR on GitHub
```

---

**Last Updated:** February 2025  
**Maintainer:** Grid Simulation Team  
**Status:** 🟡 STAGE 2 - Active Development

⭐ **Star this repository** if you find it useful!  
🐛 **Report bugs** via GitHub Issues  
💡 **Suggest features** via GitHub Discussions

---

### 🎯 Next Steps

1. **Setup the environment** (clone, install)
2. **Run Stage 2 tests** to verify installation
3. **Read PILLAR_1_DETAILS.md** to understand grid model
4. **Explore grid_model.py** and gym_grid_env.py
5. **Run a simulation** with fault injection
6. **Check CONTRIBUTING.md** if you want to help

**Ready to make grids think? Let's go! ⚡**
