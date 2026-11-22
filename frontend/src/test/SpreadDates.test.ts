import { describe, it, expect } from "vitest";
import {
  computeSpreadDates,
  generateMockSlotsForCycle,
  generateScheduleForCycle,
  applyAlgorithmToTimetable,
  addMockCycle,
} from "../services/mockData";

describe("Spread Exam Dates & Cycle Anchoring", () => {
  it("anchors the first exam date to startDate and last exam date to endDate with gaps", () => {
    const dates = computeSpreadDates("2026-12-15", "2026-12-25", 3, [1, 2, 3, 4, 5, 6]);
    expect(dates).toHaveLength(3);
    expect(dates[0]).toBe("2026-12-15");
    expect(dates[2]).toBe("2026-12-25");

    // Intermediate date should be spread in the middle (e.g. 2026-12-19 or 2026-12-21)
    const d0 = new Date(dates[0]).getTime();
    const d1 = new Date(dates[1]).getTime();
    const d2 = new Date(dates[2]).getTime();

    expect(d1).toBeGreaterThan(d0);
    expect(d2).toBeGreaterThan(d1);

    // Gaps must be greater than 1 day (not consecutive)
    const oneDay = 24 * 60 * 60 * 1000;
    expect(d1 - d0).toBeGreaterThanOrEqual(2 * oneDay);
    expect(d2 - d1).toBeGreaterThanOrEqual(2 * oneDay);
  });

  it("handles demo cycle 2026-06-10 to 2026-06-20 with 5 days gap", () => {
    const dates = computeSpreadDates("2026-06-10", "2026-06-20", 3, [1, 2, 3, 4, 5, 6]);
    expect(dates).toEqual(["2026-06-10", "2026-06-15", "2026-06-20"]);
  });

  it("generates slots spanning startDate to endDate for a custom cycle", () => {
    const newCycle = addMockCycle({
      name: "December 2026 Finals",
      startDate: "2026-12-15",
      endDate: "2026-12-25",
    });

    const slots = generateMockSlotsForCycle(newCycle.id);
    expect(slots.length).toBeGreaterThanOrEqual(6);

    // First slot must be on cycle.startDate
    expect(slots[0].date).toBe("2026-12-15");
    expect(slots[1].date).toBe("2026-12-15");

    // Core final slot must be on cycle.endDate
    expect(slots[4].date).toBe("2026-12-25");
    expect(slots[5].date).toBe("2026-12-25");

    // Middle slots must have gap days
    expect(slots[2].date).not.toBe("2026-12-15");
    expect(slots[2].date).not.toBe("2026-12-16"); // Must not be consecutive!
  });

  it("assigns exams spanning from startDate to endDate with gap days", () => {
    const newCycle = addMockCycle({
      name: "Spring Midterms 2027",
      startDate: "2027-03-01",
      endDate: "2027-03-15",
    });

    const schedule = generateScheduleForCycle(newCycle.id);
    const assignedDates = Array.from(new Set(schedule.assignments.map((a) => a.slotDate))).sort();

    expect(assignedDates[0]).toBe("2027-03-01");
    expect(assignedDates[assignedDates.length - 1]).toBe("2027-03-15");
    expect(assignedDates.length).toBe(3);
  });

  it("applies algorithm (DSATUR) to timetable with spread dates", () => {
    const newCycle = addMockCycle({
      name: "Fall Finals 2027",
      startDate: "2027-11-10",
      endDate: "2027-11-24",
    });

    const schedule = applyAlgorithmToTimetable(newCycle.id, "dsatur");
    const assignedDates = Array.from(new Set(schedule.assignments.map((a) => a.slotDate))).sort();

    expect(assignedDates[0]).toBe("2027-11-10");
    expect(assignedDates[assignedDates.length - 1]).toBe("2027-11-24");
    expect(assignedDates.length).toBe(3);
  });
});
