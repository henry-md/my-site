export type UiMode = 'light' | 'dark';

export type BackgroundConfig = {
  id: string;
  label: string;
  uiMode: UiMode;
  canvasType: 'none' | 'creepy-eye';
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
    id: 'creepy-eye',
    label: 'Creepy Eye',
    uiMode: 'dark',
    canvasType: 'creepy-eye',
    canvasOpacity: 0.2,
  },
];

export const DEFAULT_BACKGROUND_ID = 'classic';

