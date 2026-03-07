export type UiMode = 'light' | 'dark';

export type BackgroundConfig = {
  id: string;
  label: string;
  uiMode: UiMode;
  canvasType: 'creepy-eye' | 'hexagon-3d' | 'birds';
  canvasOpacity: number;
};

export const BACKGROUND_CONFIGS: BackgroundConfig[] = [
  {
    id: 'creepy-eye',
    label: 'creepy-eye',
    uiMode: 'dark',
    canvasType: 'creepy-eye',
    canvasOpacity: 0.2,
  },
  {
    id: 'hexagon-3d',
    label: 'hexagon-3d',
    uiMode: 'light',
    canvasType: 'hexagon-3d',
    canvasOpacity: 1,
  },
  {
    id: 'bird',
    label: 'bird',
    uiMode: 'light',
    canvasType: 'birds',
    canvasOpacity: 1,
  },
];

export const DEFAULT_BACKGROUND_ID = 'bird';
