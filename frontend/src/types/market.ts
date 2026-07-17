export interface Market {
  id: number;
  name: string;
  state: string;
  city: string;
  address: string;
  distanceInKilometers: number | null;
  nameColor: null | string;
  offersCount?: number;
}

export interface LocationCoordinates {
  latitude: number;
  longitude: number;
}
