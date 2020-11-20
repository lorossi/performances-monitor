class Chart {
  constructor(container, max) {
    this.container = container;
    this.max = max;
    this.color = getCssProperty("--grey-bg-color");
    this.cols = parseInt(getCssProperty("--chart-max-bars"));
    this.data = new Array(this.cols).fill(0);

    $(this.container).html("<div class='chartcontainer'></div>");
    for (let i = 0; i < this.cols; i++) {
      $(`${this.container} .chartcontainer`).append("<div class='bar'><div class='value'></div><div class='filler'></div></div>")
    }
    $(`${this.container} .bar *`).css("background-color", this.color);
  }

  addData(data) {
    this.data.unshift(data);
    this.data.pop(data);
  }

  updateChart() {
    $(`${this.container} .bar`).toArray().forEach((b, i) => {
      let height = `${this.data[i] / this.max * 100}%`;
      let complementary_height = `${100 - this.data[i] / this.max * 100}%`;
      $(b).find(".value").css("height", height);
      $(b).find(".filler").css("height", complementary_height);
    });
  }
}
