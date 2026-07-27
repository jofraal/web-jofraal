/** @type {import("tailwindcss").Config} */
module.exports = {
    content: [
        './core/templates/**/*.html',
        './products/templates/**/*.html',
        './cart/templates/**/*.html',
        './orders/templates/**/*.html',
        './users/templates/**/*.html',
    ],
    theme: {
        extend: {
            colors: {
                primary: '#3490dc',
                secondary: '#ffed4a',
                danger: '#e3342f',
            },
            screens: {
                'xs': '480px',
            },
        },
    },
    plugins: [],
}
