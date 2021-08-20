const destinationsMap = new Map();
let map, infoWindow, initialMarker;

function initMap() {
  let options = {
    center: { lat: 25.34, lng: 137.8 },
    zoom: 2.5,
    disableDefaultUI: true,
    zoomControl: true,
    mapTypeId: "roadmap",
  };

  map = new google.maps.Map(document.getElementById("map"), options);

  infoWindow = new google.maps.InfoWindow();

  //Set map to current location
  initLocationButton(map);

  // Setup directions service
  const directionsService = new google.maps.DirectionsService();
  const directionsRenderer = new google.maps.DirectionsRenderer({
    draggable: true,
    map,
  });
  const geocoder = new google.maps.Geocoder();
  directionsRenderer.addListener("directions_changed", () => {
    const directions = directionsRenderer.getDirections();

    if (directions) {
      computeTotalDistance(directions);
    }
    geocodeAddress(geocoder, directionsRenderer);
    updateList();
  });

  map.addListener("click", async (mapsMouseEvent) => {
    await addElementToMap(geocoder, mapsMouseEvent.latLng);
    await toggleMarker(mapsMouseEvent.latLng, map);
    await displayRoute(directionsService, directionsRenderer);
  });

  autocomplete(geocoder, map, directionsService, directionsRenderer);
}
//Disable the default markers (keep the directions markers)
function toggleMarker(latLng, map) {
  if (destinationsMap.size < 2) placeMarker(latLng, map);
  else if (destinationsMap.size == 2) initialMarker.setMap(null);
}

function initLocationButton(map) {
  const locationButton = document.createElement("button");
  locationButton.textContent = "Go to Current Location";
  locationButton.classList.add("custom-map-control-button");
  map.controls[google.maps.ControlPosition.TOP_CENTER].push(locationButton);
  locationButton.addEventListener("click", () => {
    moveToCurrentLocation(infoWindow);
  });
}

/*
  API Requests
*/
function fetchDestinations() {
  fetch("http://localhost:5000/api/create_destination/1").then((data) =>
    data.json()
  );
  //Set destinations map by iterating through data
  //call in init
}

function saveDestinations() {
  if (destinationsMap.size > 0) {
    let destinationsArr = [];
    destinationsMap.forEach((value, key) => {
      destinationsArr.push({ order: key, location_data: value });
    });
    let data = JSON.stringify(destinationsArr);

    fetch("http://localhost:5000/api/destination/1", {
      method: "POST",
      body: data,
    }).then((res) => {
      console.log("Request complete! response:", res);
    });
  }
}

/*
  Move map to current location
*/
function moveToCurrentLocation(infoWindow) {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const pos = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        infoWindow.setPosition(pos);
        infoWindow.setContent("Location found.");
        infoWindow.open(map);
        map.setCenter(pos);
        map.setZoom(8);
      },
      () => {
        handleLocationError(true, infoWindow, map.getCenter());
      }
    );
  } else {
    // Browser doesn't support Geolocation
    handleLocationError(false, infoWindow, map.getCenter());
  }
}

/*
  Directions service
*/
async function displayRoute(service, display) {
  let waypoints = [];
  //Create list of stops without origin and destination
  let counter = 1;
  if (destinationsMap.size > 2) {
    for (const [key, value] of destinationsMap.entries()) {
      if (counter != 1 && counter != destinationsMap.size)
        waypoints.push(value.coordinate);
      counter++;
    }
  }

  if (destinationsMap.size > 1) {
    service
      .route({
        origin: getFirstValue(),
        destination:
          destinationsMap.size > 1
            ? getLastValue().coordinate.location
            : undefined,
        waypoints: waypoints ? [...waypoints] : undefined,
        travelMode: google.maps.TravelMode.DRIVING,
        avoidTolls: true,
      })
      .then((result) => {
        display.setDirections(result);
      })
      .catch((e) => {
        alert("Could not display directions due to: " + e);
      });
  }
}
/*
  Add drag event listener to dragable markers
*/
function geocodeAddress(geocoder, display) {
  display.directions.geocoded_waypoints.forEach((waypoint) => {
    geocoder
      .geocode({ placeId: waypoint.place_id })
      .then(({ results }) => checkvals(results[0]));
  });
}

let addressByCoordinates = function (geocoder, coordinates) {
  return geocoder
    .geocode({ location: coordinates })
    .then(({ results }) => {
      return results[0];
    })
    .catch((e) =>
      alert("Geocode was not successful for the following reason: " + e)
    );
};

function checkvals(waypoint) {
  let exists = false;
  let missingKey = undefined;

  for (const [key, value] of destinationsMap.entries()) {
    if (waypoint.place_id.localeCompare(value.place_id) !== 0) {
      missingKey = key;
      exists = true;
    }
  }
  if (missingKey)
    buildMap(
      missingKey,
      waypoint.place_id,
      waypoint.formatted_address,
      waypoint.geometry.location
    );
}

/*
  Add a marker on the map
*/
function placeMarker(latLng, map) {
  let content; //content = function
  //CREATE FUNCTION THAT REQUEST DATA FROM GEOCODING API move to function
  fetch(
    `https://maps.googleapis.com/maps/api/geocode/json?latlng=${latLng.lat()},${latLng.lng()}&key=AIzaSyC36j1eUXC0390oR1U3joY7onMSuqBU_U0`
  )
    .then((res) => res.json())
    .then((data) => {
      if (data.results.length) content = data.results[0].formatted_address;
      else content = latLng.lat() + ", " + latLng.lng();
    })
    .catch((e) => console.log("invalid address"));
  let marker = new google.maps.Marker({
    position: latLng,
    map: map,
  });
  initialMarker = marker;

  google.maps.event.addListener(marker, "click", function (event) {
    infoWindow.close();
    //If Alias then content = alias, else content = city,country of the location
    infoWindow.setContent(`${content}`);
    infoWindow.open(map, marker);
  });
  // map.panTo(latLng);
}

/*
  Get distance between locations
*/
function computeTotalDistance(result) {
  let total = 0;
  const myroute = result.routes[0];

  if (!myroute) {
    return;
  }

  for (let i = 0; i < myroute.legs.length; i++) {
    total += myroute.legs[i].distance.value;
  }
  total = total / 1000;

  document.getElementById("total-distance").value = total + " km";
  //TODO: ADD TIME
}

/*
  Autocomplete
*/
function autocomplete(geocoder, map, service, display) {
  // Create the search box and link it to the UI element.
  const input = document.getElementById("pac-input");
  const searchBox = new google.maps.places.SearchBox(input);
  // Bias the SearchBox results towards current map's viewport.
  map.addListener("bounds_changed", () => {
    searchBox.setBounds(map.getBounds());
  });
  // Listen for the event fired when the user selects a prediction and retrieve
  // more details for that place.
  searchBox.addListener("places_changed", () => {
    const places = searchBox.getPlaces();

    if (places.length == 0) {
      return;
    }

    const bounds = new google.maps.LatLngBounds();
    places.forEach(async (place) => {
      if (!place.geometry || !place.geometry.location) {
        console.log("Returned place contains no geometry");
        return;
      }

      await addElementToMap(geocoder, place.geometry.location);
      await toggleMarker(place.geometry.location, map);
      await displayRoute(service, display);

      if (place.geometry.viewport) {
        // Only geocodes have viewport.
        bounds.union(place.geometry.viewport);
      } else {
        bounds.extend(place.geometry.location);
      }
    });
    map.fitBounds(bounds);
  });
}

/*
  Handle Errors
*/
function handleLocationError(browserHasGeolocation, infoWindow, pos) {
  infoWindow.setPosition(pos);
  infoWindow.setContent(
    browserHasGeolocation
      ? "Error: The Geolocation service failed."
      : "Error: Your browser doesn't support geolocation."
  );
  infoWindow.open(map);
}

/*
  Add HTML content
*/
function updateList() {
  document.getElementById("destinations-list").replaceChildren();
  let node = document.createElement("LI");
  for (const [key, value] of destinationsMap.entries()) {
    node.className += `destination-${key}`;
    let textnode = document.createTextNode(`${key}, ${value.area_name}`); // do reverse geocoding
    node.appendChild(textnode);
    document.getElementById("destinations-list").appendChild(node);
  }
}

async function addElementToMap(geocoder, coordinates) {
  let place = await addressByCoordinates(geocoder, coordinates);

  if (destinationsMap.size == 0)
    buildMap(1, place.place_id, place.formatted_address, coordinates);
  else
    buildMap(
      getLastKey() + 1,
      place.place_id,
      place.formatted_address,
      coordinates
    );
}

function buildMap(key, place, areaName, coordinates) {
  destinationsMap.set(key, {
    place_id: place,
    area_name: areaName,
    coordinate: { location: coordinates },
  });
}
const getLastKey = () => Array.from(destinationsMap.keys()).pop();
const getFirstValue = () =>
  destinationsMap.values().next().value.coordinate.location;
const getLastValue = () => [...destinationsMap][destinationsMap.size - 1][1];
