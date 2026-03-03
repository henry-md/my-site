export type UiMode = 'light' | 'dark';

export type BackgroundConfig = {
  id: string;
  label: string;
  uiMode: UiMode;
  canvasType: 'none' | 'hexagon-3d';
  canvasOpacity: number;
};

export const BACKGROUND_CONFIGS: BackgroundConfig[] = [
  {
    id: 'classic',
    label: 'Classic',
    uiMode: 'light',
    canvasType: 'none',
    canvasOpacity: 0,
  },
  {
    id: 'hexagon-3d',
    label: 'hexagon-3d',
    uiMode: 'light',
    canvasType: 'hexagon-3d',
    canvasOpacity: 1,
  },
];

export const DEFAULT_BACKGROUND_ID = 'hexagon-3d';
