const CDN = "https://media.formula1.com/image/upload";

export const driverPhoto = (
  year: number,
  team: string,
  code: string,
  size = 440
): string =>
  `${CDN}/c_fill,w_${size}/q_auto/d_common:f1:${year}:fallback:driver:${year}fallbackdriverright.webp/v1/common/f1/${year}/${team}/${code}/${year}${team}${code}right.webp`;

export const teamCar = (
  year: number,
  team: string,
  size = 512
): string =>
  `${CDN}/c_fill,w_${size}/q_auto/v1/common/f1/${year}/${team}/${year}${team}car.webp`;

export const teamLogo = (
  year: number,
  team: string,
  size = 200
): string =>
  `${CDN}/c_fill,w_${size}/q_auto/v1/common/f1/${year}/${team}/${year}${team}logo.webp`;
