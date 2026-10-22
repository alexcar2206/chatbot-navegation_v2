export type FeatureNavegacion = 'mapa' | 'declaracion';

/**
 * A navigation feature is usable when it is enabled globally (admin settings)
 * and the user is an admin or has the `features.<feature>` group permission.
 * Mirrors the backend dependency in navegacion/deps.py.
 */
export const featureNavegacionDisponible = (
	config: any,
	user: any,
	feature: FeatureNavegacion
): boolean =>
	Boolean(config?.features?.[`enable_${feature}`] ?? false) &&
	(user?.role === 'admin' || (user?.permissions?.features?.[feature] ?? true));
