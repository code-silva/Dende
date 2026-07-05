export function formatDistance(
  distanceInKilometers: number | null | undefined,
): string | null {
  if (distanceInKilometers == null) return null;

  if (distanceInKilometers < 1) {
    const meters = Math.round(distanceInKilometers * 1000);
    return `${meters}m`;
  }

  const km = distanceInKilometers.toFixed(1).replace(".", ",");
  return `${km} km`;
}
