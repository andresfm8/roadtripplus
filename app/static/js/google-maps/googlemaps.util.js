let map, infoWindow;

function initMap() {
  //TODO: Pass locations in markers and then use reverse geocoding to get their locations
  let destinations = [{ location: "Perth, WA" }, { location: "Sydney, NSW" }, { location: "Adelaide, SA" }, { location: "Broken Hill, NSW" }];

  let options = {
    // TO DO: Set the location to be your location if user allows location usage
    // Else set a random location?
    center: { lat: 25.34, lng: 137.80 },
    zoom: 2.5,
    disableDefaultUI: true,
    zoomControl: true,
  }

  map = new google.maps.Map(document.getElementById("map"), options);

  infoWindow = new google.maps.InfoWindow();

  /*
    Set map to current location
  */
  const locationButton = document.createElement("button");
  locationButton.textContent = "Go to Current Location";
  locationButton.classList.add("custom-map-control-button");
  map.controls[google.maps.ControlPosition.TOP_CENTER].push(locationButton);
  locationButton.addEventListener("click", () => {
    moveToCurrentLocation(infoWindow);
  });

  /*
    TODO:
        - Add event click listener that asks "ADD LOCATION AS DESTINATION?"
          It could be a + button in thr marker infowindow
  */

  map.addListener("click", (mapsMouseEvent) => {
    placeMarker(mapsMouseEvent.latLng, map);
  });

  /*
    Direction setup
  */
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

  displayRoute(destinations, directionsService, directionsRenderer);
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
function displayRoute(destinations, service, display) {

  let arr = [];
  for (let i = 1; i < destinations.length - 1; i++) {
    arr = [...arr, destinations[i]];
  }

  console.log(destinations[0])
  service
    .route({
      //ORIGIN will be first item in the list, DESTINATION will be last
      origin: destinations[0].location,
      destination: destinations[destinations.length - 1].location,
      waypoints: [...arr],
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

/*
  Add a marker on the map
*/

function placeMarker(latLng, map) {
  let marker = new google.maps.Marker({
    position: latLng,
    map: map,
  });

  google.maps.event.addListener(marker, "click", function (event) {
    let latitude = event.latLng.lat();
    let longitude = event.latLng.lng();
    infoWindow.close();
    //If Alias then content = alias, else content = city,country of the location
    infoWindow.setContent(`${latitude}, ${longitude}`);
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