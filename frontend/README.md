# Supercluster Frontend

This is a React-based frontend for the Supercluster API, providing a map visualization of clustered geospatial data.

## Features

- Interactive Mapbox GL map with clustering visualization
- Toggle different map layers on/off
- Filter data by various criteria (gender, country, etc.)
- Real-time cluster updates as you navigate the map
- Point information displayed in popups

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

## API Integration

The frontend interfaces with the FastAPI-based Supercluster API. It uses relative URLs and a proxy configuration to communicate with the backend running on `http://localhost:8000`.

## Required Environment Variables

- `REACT_APP_MAPBOX_ACCESS_TOKEN`: Your Mapbox GL access token (required for map rendering)

## Dependencies

- React 18.x
- Mapbox GL JS 2.x
- React Map GL 7.x
- Axios for API communication 