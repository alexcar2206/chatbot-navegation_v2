import { describe, expect, it } from 'vitest';
import {
	contarPorEstado,
	distanciaKm,
	filtrarZonas,
	filtrosAUrl,
	filtrosDesdeUrl,
	filtrosVacios,
	ordenarZonas,
	type ZonaFeature
} from './filtros';

const feat = (props: Record<string, unknown>): ZonaFeature => ({
	type: 'Feature',
	properties: props
});

const ZONAS: ZonaFeature[] = [
	feat({
		_nombre: 'ALBARELLOS',
		_estado: 'permitida',
		_mvp: 'Albarellos',
		_rio: 'AVIA',
		_usos: ['hidroelectrico'],
		_superficie_ha: 314,
		_volumen_hm3: 90,
		_plazo_anios: 6,
		_centroide: [42.0, -8.0]
	}),
	feat({
		_nombre: 'BARCENA',
		_estado: 'restringida',
		_mvp: null,
		_rio: 'SIL',
		_usos: ['riego'],
		_superficie_ha: 100,
		_volumen_hm3: 20,
		_plazo_anios: 1,
		_centroide: [42.6, -6.6]
	}),
	feat({
		_nombre: 'PEÑADRADA',
		_estado: 'prohibida',
		_mvp: null,
		_rio: 'SIL',
		_usos: [],
		_superficie_ha: null,
		_volumen_hm3: null,
		_plazo_anios: null,
		_centroide: [42.5, -6.7]
	}),
	feat({
		_nombre: 'SANTO ESTEVO',
		_estado: 'ponars',
		_mvp: 'Santo Estevo',
		_rio: 'MIÑO',
		_usos: ['hidroelectrico'],
		_superficie_ha: 200,
		_volumen_hm3: 50,
		_plazo_anios: 1,
		_centroide: [42.4, -7.6]
	})
];

describe('filtrarZonas', () => {
	it('filters by status set', () => {
		const f = filtrosVacios();
		f.estados = new Set(['permitida', 'ponars']);
		const out = filtrarZonas(ZONAS, f);
		expect(out.map((z) => z.properties?._nombre)).toEqual(['ALBARELLOS', 'SANTO ESTEVO']);
	});

	it('filters MVP only', () => {
		const f = filtrosVacios();
		f.soloMvp = true;
		expect(filtrarZonas(ZONAS, f)).toHaveLength(2);
	});

	it('filters by query ignoring accents', () => {
		const f = filtrosVacios();
		f.q = 'penadra';
		expect(filtrarZonas(ZONAS, f)[0]?.properties?._nombre).toBe('PEÑADRADA');
	});

	it('filters by use and river', () => {
		const f = filtrosVacios();
		f.usos = new Set(['riego']);
		f.rio = 'SIL';
		expect(filtrarZonas(ZONAS, f).map((z) => z.properties?._nombre)).toEqual(['BARCENA']);
	});
});

describe('ordenarZonas', () => {
	it('orders by status severity', () => {
		const out = ordenarZonas(ZONAS, 'estado', 'asc');
		expect(out.map((z) => z.properties?._estado)).toEqual([
			'permitida',
			'restringida',
			'ponars',
			'prohibida'
		]);
	});

	it('orders by surface descending', () => {
		const out = ordenarZonas(ZONAS, 'superficie', 'desc');
		expect(out[0]?.properties?._nombre).toBe('ALBARELLOS');
	});

	it('orders by distance when origin is set', () => {
		const out = ordenarZonas(ZONAS, 'distancia', 'asc', { lat: 42.0, lon: -8.0 });
		expect(out[0]?.properties?._nombre).toBe('ALBARELLOS');
	});
});

describe('URL sync', () => {
	it('round-trips filters', () => {
		const f = filtrosVacios();
		f.q = 'bel';
		f.estados = new Set(['permitida', 'restringida']);
		f.soloMvp = true;
		f.usos = new Set(['riego']);
		f.rio = 'Sil';
		f.orden = 'superficie';
		f.dir = 'desc';
		const params = filtrosAUrl(f);
		const back = filtrosDesdeUrl(params);
		expect(back.q).toBe('bel');
		expect([...back.estados].sort()).toEqual(['permitida', 'restringida']);
		expect(back.soloMvp).toBe(true);
		expect([...back.usos]).toEqual(['riego']);
		expect(back.rio).toBe('Sil');
		expect(back.orden).toBe('superficie');
		expect(back.dir).toBe('desc');
	});
});

describe('helpers', () => {
	it('counts statuses', () => {
		expect(contarPorEstado(ZONAS)).toEqual({
			permitida: 1,
			restringida: 1,
			prohibida: 1,
			ponars: 1,
			sin_datos: 0
		});
	});

	it('computes haversine roughly', () => {
		const km = distanciaKm({ lat: 42, lon: -8 }, { lat: 42, lon: -8 });
		expect(km).toBeCloseTo(0, 5);
	});
});
