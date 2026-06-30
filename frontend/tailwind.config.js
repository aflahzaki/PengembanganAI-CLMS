/** @type {import('tailwindcss').Config} */
export default {
	darkMode: 'class',
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				primary: {
					DEFAULT: '#003d7a',
					50: '#e6f0fa',
					100: '#b3d4f0',
					200: '#80b8e6',
					300: '#4d9cdb',
					400: '#1a80d1',
					500: '#003d7a',
					600: '#003163',
					700: '#00254c',
					800: '#001936',
					900: '#000d1f'
				}
			}
		}
	},
	plugins: []
};
