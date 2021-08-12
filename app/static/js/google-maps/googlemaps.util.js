/** TODO: 
 * Button to set current location as origin
 * Generate list of destinations
 * Remove + button
*/

let map, infoWindow, initialMarker;
let destinations = [];

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
    destinations.push({ location: mapsMouseEvent.latLng });
    toggleMarker(mapsMouseEvent.latLng, map);
    displayRoute(directionsService, directionsRenderer);
  });

  autocomplete(map, directionsService, directionsRenderer);
}

function toggleMarker(latLng, map) {
  if (destinations.length < 2)
    placeMarker(latLng, map);
  else if (destinations.length == 2) {
    initialMarker.setMap(null);
  }
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
  if (destinations.length > 2) {
    for (let i = 1; i < destinations.length - 1; i++)
      waypoints.push(destinations[i]);
  }
  if (destinations.length > 1) {
    service
      .route({
        //ORIGIN will be first item in the list, DESTINATION will be last
        origin: destinations[0].location,
        destination: destinations.length > 1 ? destinations[destinations.length - 1].location : undefined,
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
      console.log(place.geometry.location);
      //ADD TO destinations?
      destinations.push({ location: place.geometry.location });
      toggleMarker(place.geometry.location, map);
      displayRoute(service, display);
      // Create a marker for each place.
      // placeMarker(place.geometry.location, map, place.name);

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