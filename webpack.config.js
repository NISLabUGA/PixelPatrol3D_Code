const path = require('path');
const CopyPlugin = require('copy-webpack-plugin');

module.exports = {
  mode: 'development', // or "production" when ready
  entry: {
    popup: './src/popup.js',
    background: './src/background.js',
    sandbox: './src/sandbox.js',
    onnx_worker: './src/onnx_worker.js',
    offscreen: './src/offscreen.js',
    notification: './src/notification.js',
    utils: './src/utils.js',
  },
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].js',
    library: { type: 'module' },
  },
  experiments: {
    outputModule: true,
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env'],
          },
        },
      },
    ],
  },
  plugins: [
    new CopyPlugin({
      patterns: [
        { from: 'public', to: '.' }, // Copies manifest.json, popup.html, popup.css, etc.
      ],
    }),
  ],
  devtool: 'cheap-module-source-map', // For easier debugging
  devServer: {
    static: path.join(__dirname, 'dist'),
    hot: true,
    liveReload: true,
    watchFiles: ['src/**/*', 'public/**/*'],
    devMiddleware: {
      writeToDisk: true, // Ensure files are written to disk
    },
  },
};
