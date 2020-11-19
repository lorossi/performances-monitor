let refresh_interval;

$(document).ready(function() {
  refresh_interval = 5000;
  dt = 2000;

  getStats(250);
  getNetwork();

  setInterval(getStats, refresh_interval, dt);
});

function getNetwork() {
  $.ajax({
    type : 'POST',
    url : '/getnetwork/',
    complete : function(response) {
      if (response.status == 200) {
        for (let property in response.responseJSON) {
          $(`#${property} .statvalue`).text(response.responseJSON[property]);
        }
      }
    }
  });
}

function getStats(dt) {
  $.ajax({
    type : 'POST',
    url : '/getstats/',
    data: {"dt": dt},
    complete : function(response) {
      if (response.status == 200) {
        for (let property in response.responseJSON) {
          $(`#${property} .statvalue`).text(response.responseJSON[property].text);
          $(`#${property}`).css({
            "background-color": response.responseJSON[property].color
          });
        }
      }
    }
  });
}
