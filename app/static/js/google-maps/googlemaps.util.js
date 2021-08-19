/** TODO: 
 * Button to set current location as origin
 * Generate list of destinations
 * Remove + button
 * Create array and push each marker to it
 * Assign an id or some identifier to each marker and 
 * If the marker is moved then updated the value
 * If the marker is removed then update the order and remove from markerlist?
 * How to get markers of directions
 * IDEA: SAVE EACH WAYPOINT AS WELL AS ORIGIN AND DESTINATION
 * WHEN? ANYTHING CHANGES, THEN LOOK FOR THE ONE THAT JUST CHANGED (WITH THE TRACKER probs a hashmap)
 * THEN UPDATE AND SET DIRECTIONS AGAIN -> Basically will have to re-render directions, sucks but depends on gmaps api
*/

//Key: Order, Value: Coordinates
const destinationsMap = new Map();
let map, infoWindow, initialMarker;

function initMap() {
  let options = {
    // TO DO: Set the location to be your location if user allows location usage
    // Else set a random location?
    center: { lat: 25.34, lng: 137.80 },
    zoom: 2.5,
    disableDefaultUI: true,
    zoomControl: true,
    mapTypeId: "roadmap"
  }

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

  directionsRenderer.addListener("directions_changed", () => {
    const directions = directionsRenderer.getDirections();

    if (directions) {
      computeTotalDistance(directions);
    }
  });

  map.addListener("click", (mapsMouseEvent) => {
    addElementToMap(mapsMouseEvent.latLng);
    toggleMarker(mapsMouseEvent.latLng, map);
    displayRoute(directionsService, directionsRenderer);
  });

  autocomplete(map, directionsService, directionsRenderer);
}
//Disable the default markers (keep the directions markers)
function toggleMarker(latLng, map) {
  if (destinationsMap.size < 2)
    placeMarker(latLng, map);
  else if (destinationsMap.size == 2)
    initialMarker.setMap(null);
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
  Move map to current location
*/
function moveToCurrentLocation(infoWindow) {
  // TODO: Replace info window with marker
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
function displayRoute(service, display) {
  let waypoints = [];
  //Create list of stops without origin and destination
  let counter = 1;
  if (destinationsMap.size > 2) {
    for (const [key, value] of destinationsMap.entries()) {
      if (counter != 1 && counter != destinationsMap.size)
        waypoints.push(value)
      counter++;
    }
  }

  if (destinationsMap.size > 1) {
    service
      .route({
        origin: getFirstValue().location,
        destination: destinationsMap.size > 1 ? getLastValue().location : undefined,
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
  Add a marker on the map
*/
function placeMarker(latLng, map) {

  let content;//content = function
  //CREATE FUNCTION THAT REQUEST DATA FROM GEOCODING API move to function
  fetch(`https://maps.googleapis.com/maps/api/geocode/json?latlng=${latLng.lat()},${latLng.lng()}&key=AIzaSyC36j1eUXC0390oR1U3joY7onMSuqBU_U0`)
    .then(res => res.json())
    .then(data => {
      if (data.results.length) content = data.results[0].formatted_address;
      else content = latLng.lat() + ", " + latLng.lng();
    })
    .catch(e => console.log("invalid address"))
  let marker = new google.maps.Marker({
    position: latLng,
    map: map,
  });
  initialMarker = marker;

  google.maps.event.addListener(marker, "click", function (event) {
    // let latitude = event.latLng.lat();
    // let longitude = event.latLng.lng();
    infoWindow.close();
    //If Alias then content = alias, else content = city,country of the location
    infoWindow.setContent(`${content}`);
    infoWindow.open(map, marker);
  });
  // map.panTo(latLng);
  google.maps.event.addListener(marker, "drag", function (event) {
    console.log("drag");
  });

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
  // document.getElementById("total").innerHTML = total + " km";
}

/*
  Autocomplete
*/
function autocomplete(map, service, display) {
  // Create the search box and link it to the UI element.
  //TODO: Search box has to be dynamic -> execute autocomplete on the searchbox that is called
  const input = document.getElementById("pac-input");
  const searchBox = new google.maps.places.SearchBox(input);
  // map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
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
    places.forEach((place) => {
      if (!place.geometry || !place.geometry.location) {
        console.log("Returned place contains no geometry");
        return;
      }

      addElementToMap(place.geometry.location);
      toggleMarker(place.geometry.location, map);
      displayRoute(service, display);

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
function updateList(key, value) {
  let node = document.createElement("LI");
  let textnode = document.createTextNode(`${key}, ${value.location}`);// do reverse geocoding
  node.appendChild(textnode);
  document.getElementById("destinations-list").appendChild(node);
}

//destinationMaps util functions
function addElementToMap(coordinates) {
  if (destinationsMap.size == 0)
    destinationsMap.set(1, { location: coordinates });
  else {
    destinationsMap.set(getLastKey() + 1, { location: coordinates })
  }
  updateList(getLastKey(), getLastValue());
}
const getLastKey = () => Array.from(destinationsMap.keys()).pop();
const getFirstValue = () => destinationsMap.values().next().value;
const getLastValue = () => [...destinationsMap][destinationsMap.size - 1][1];