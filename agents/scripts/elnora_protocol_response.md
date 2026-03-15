# Automated iPSC-fast Passaging and Harvest Protocol

## Objective
To achieve maximum cell yield (**~15M cells**) over a 3-day culture period using the **iPSC-fast** cell line in a **T175 flask**. This protocol utilizes an automated workcell, enzyme-free dissociation (ReLeSR), and room-temperature media to maintain cell viability and pluripotency while strictly adhering to time-out-of-incubator constraints.

---

## Key Parameters & Critical Constraints

| Parameter | Value |
| :--- | :--- |
| **Cell Line** | iPSC-fast (Doubling time: **~16 hours**) |
| **Labware** | 1x T175 flask (**175 cm²**) |
| **Seeding Density** | **15,000 cells/cm²** (**2.625M total cells**) |
| **Target Yield** | **~15M cells** at Day 3 |
| **Media** | Media A (**ROOM TEMPERATURE ONLY** - Do **NOT** warm) |
| **Dissociation Reagent** | ReLeSR (Enzyme-free) |
| **Feeding Schedule** | Every **24 hours** (Full media change, **35 mL**) |
| **Confluency Limits** | Max before passage: **70%** \| Target at harvest: **80%** |
| **Time Constraint** | Flask must **NOT exceed 15 minutes** outside the incubator |

---

## Materials & Equipment

### Reagents & Consumables
*   **Media A** (Equilibrated to Room Temperature)
*   **ReLeSR** Dissociation Reagent
*   T175 Tissue Culture Treated Flasks
*   **50 mL** Falcon Tubes
*   Sterile pipette tips (compatible with automated pipette station)

### Workcell Equipment
*   UR12e Robot Arm with Robotiq Gripper
*   Automated Pipette Station
*   Automated CO₂ Incubator (**37°C, 5% CO₂**)
*   Biological Safety Cabinet (BSC)
*   Automated Microscope / Imaging Station

---

## 3-Day Schedule Overview

| Day | Action | Target Confluency | Media Volume |
| :--- | :--- | :--- | :--- |
| **Day 0** | Initial Seeding | ~10-15% | **35 mL** |
| **Day 1** | Daily Feed (24h) | ~25-35% | **35 mL** |
| **Day 2** | Daily Feed (48h) | ~50-60% | **35 mL** |
| **Day 3** | Harvest & Re-seed (72h) | **80%** | **35 mL** (New Flask) |

---

## Step-by-Step Procedure

### Part 1: Daily Feeding (Days 1 & 2)
*Execute every 24 hours. Ensure the entire cycle completes in **< 15 minutes**.*

1.  **Retrieve Flask:** UR12e robot arm transfers the T175 flask from the **37°C incubator** to the microscope.
2.  **Image & QC:** Capture images to verify confluency.
    *   *Note: Confluency must remain **< 70%** during the growth phase to prevent spontaneous differentiation.*
3.  **Transfer to BSC:** Move the flask to the pipette station inside the BSC.
4.  **Aspirate Media:** Completely aspirate the spent media from the flask.
5.  **Add Fresh Media:** Dispense **35 mL** of **Room Temperature Media A** gently against the side of the flask to avoid disturbing the cell monolayer.
6.  **Return to Incubator:** UR12e robot arm transfers the flask back to the **37°C, 5% CO₂** incubator.

### Part 2: Harvest & Dissociation (Day 3)
*Execute at 72 hours post-seeding. Target confluency is **80%**.*

1.  **Retrieve & Verify:** Transfer the T175 flask to the microscope. Verify confluency has reached the **80%** target.
2.  **Transfer to BSC:** Move the flask to the pipette station.
3.  **Aspirate Media:** Completely aspirate the spent media.
4.  **Add ReLeSR:** Dispense **6 mL** of ReLeSR reagent into the flask, ensuring the entire cell layer is covered.
5.  **Immediate Aspiration:** Aspirate the ReLeSR reagent completely **within 1 minute** of addition.
6.  **Incubate:** Transfer the flask back to the **37°C incubator** for exactly **6 to 8 minutes**.
7.  **Mechanical Detachment:** Retrieve the flask from the incubator. Use the robot arm/gripper to perform **fast tapping** on the side of the flask to detach the cells.
8.  **Resuspension:** Add **10 mL** of **Room Temperature Media A** to the flask. Wash the growth surface to collect the detached cell aggregates.
9.  **Collection:** Transfer the 10 mL cell suspension into a sterile **50 mL Falcon tube**.

### Part 3: Cell Counting & Re-seeding (Day 3)

1.  **Count Cells:** Take a small aliquot from the **50 mL Falcon tube** to determine cell concentration and total yield (Expected yield: **~15M cells**).
2.  **Calculate Seeding Volume:** Calculate the volume of cell suspension required to obtain exactly **2.625M cells** (for a seeding density of **15,000 cells/cm²**).
3.  **Prepare New Flask:**
    *   Transfer the calculated cell volume into a **new T175 flask**.
    *   Add **Room Temperature Media A** to bring the final volume in the flask to exactly **35 mL**.
4.  **Distribute Cells:** Gently rock the flask (cross-motion: left-to-right, top-to-bottom) to ensure even distribution of cell aggregates.
5.  **Incubate:** Transfer the new T175 flask to the **37°C, 5% CO₂** incubator.
6.  **Store/Process Remaining Cells:** The remaining cells in the **50 mL Falcon tube** (~12.3M cells) are now ready for downstream assays, cryopreservation, or delivery.

---

## Troubleshooting & Critical Notes

*   **Temperature Shock Prevention:** iPSC-fast cells are sensitive to temperature fluctuations. The strict adherence to **Room Temperature Media A** prevents the degradation of heat-sensitive factors in the media, while the **< 15 minute** out-of-incubator rule prevents the flask from cooling excessively.
*   **ReLeSR Timing:** Leaving ReLeSR on the cells for longer than **1 minute** before aspiration will over-digest the surface proteins, leading to single-cell dissociation rather than the desired small aggregates, which severely impacts iPSC viability.
*   **Fast Tapping:** If cells do not detach after the 6-8 minute incubation and fast tapping, do *not* add more ReLeSR. Add the resuspension media and use slightly more vigorous pipetting to wash them off the surface.
