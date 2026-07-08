import humanInterval from "human-interval";

/**
 * @param {number} ms - milliseconds
 * @returns {object} - object with days, hours, minutes and seconds
 * @example
 * intervalToDuration(1000) // { days: 0, hours: 0, minutes: 0, seconds: 1 }
 */
const intervalToDuration = (ms: number) => {
  let seconds = Math.floor(ms / 1000);
  const days = Math.floor(seconds / (24 * 3600));
  seconds %= 24 * 3600;
  const hours = Math.floor(seconds / 3600);
  seconds %= 3600;
  const minutes = Math.floor(seconds / 60);
  seconds %= 60;
  return {
    days,
    hours,
    minutes,
    seconds,
  };
};

const intervalToISODuration = (intervalNumber: number): string => {
  const duration = intervalToDuration(intervalNumber);
  return `P${duration.days}DT${duration.hours}H${duration.minutes}M${duration.seconds}S`;
};

// return ISO 8601 duration only using days, hours, minutes and seconds
export const humanIntervalToISODuration = (intervalString: string): string | null => {
  const intervalNumber = humanInterval(intervalString);
  return intervalNumber ? intervalToISODuration(intervalNumber) : null;
};
