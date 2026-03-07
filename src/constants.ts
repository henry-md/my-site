export const ABOVE_FOLD_TEXT_SHIMMERS = false;
export const DEBUG_UI =
  String(
    (import.meta as ImportMeta & { env: { VITE_DEBUG_UI?: string } }).env.VITE_DEBUG_UI
  ).toLowerCase() === 'true';
export const LIGHT_THEME_COLOR_GRADIENT = {
  start: '#fff',
  end: '#fff',
};

export const TESTIMONIAL_COLLAPSED_MAX_HEIGHT_PX = 420;
export const TESTIMONIAL_DESKTOP_BREAKPOINT_PX = 800;
export const TESTIMONIAL_SPACE_BETWEEN_PX = 24;

export const MOBILE_NAV_BREAKPOINT_PX = 900;
