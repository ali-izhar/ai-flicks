const img = new Image();
img.src = document.getElementById('result_image').src;
img.onload = function() {
    const imgWidth = this.width;
    const imgHeight = this.height;

    canvas.width = imgWidth;
    canvas.height = imgHeight;
}

// Define the button and canvas variables
const button = document.getElementById('buy_button');
const canvas = document.getElementById('drawing_canvas');
const context = canvas.getContext('2d');
const imageElement = document.getElementById('result_image');

// Function to draw the initial image onto the canvas
function drawInitialImage() {
    let img = new Image();
    img.src = imageElement.src;
    img.onload = function() {
        context.drawImage(img, 0, 0, canvas.width, canvas.height);
    };
}
drawInitialImage();

// Add a click handler to the button
button.addEventListener('click', (e) => {
  e.preventDefault();
  
  // Export the base64 image from the canvas
  const base64_image = canvas.toDataURL();
  
  const apiKey = 'P3sbXrqgozFxB1SwZaFbCYwiKIL7Jy6g8rDcHRUj'; 
  const options = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      image_url: base64_image,
      item_code: "RNA1",
      name: "Hello World",
      colours: "White,Black",
      description: "Check out this awesome doodle tee, printed on an organic cotton t-shirt sustainably, using renewable energy. Created via the Teemill API and printed on demand.",
      price: 20.00,
    }),
  };
  
  var newTab = window.open('about:blank', '_blank');
  newTab.document.write(
    "<body style='background-color:#faf9f9;width:100%;height:100%;margin:0;position:relative;'><img src='https://storage.googleapis.com/teemill-dev-image-bucket/doodle2tee_loader.gif' style='position:absolute;top:calc(50% - 100px);left:calc(50% - 100px);'/></body>"
  );

  fetch('https://teemill.com/omnis/v3/product/create', options)
    .then(response => response.json())
    .then(response => newTab.location.href = response.url)
    .catch(err => console.error(err));
  
});

let color = '#df1aae';
const colorPicker = document.getElementById('color_picker');
colorPicker.addEventListener('input', () => {
  color = colorPicker.value;
})

canvas.width = 1000;
canvas.height = 1300;

var drawingMode = false;
var lastEvent = null;
var lastSize = 0;
var maxSize = 15;
var minSize = 2;

function drawCircle(x, y, radius, color) {
  context.fillStyle = color;
  context.beginPath();
  const canvasRect = canvas.getBoundingClientRect();
  const canvasScale = canvas.width / canvasRect.width;
  context.save();
  context.scale(canvasScale, canvasScale);
  context.arc(
    x - canvasRect.x,
    y - canvasRect.y,
    radius, 0,
    Math.PI * 2,
  );
  context.fill();
  context.closePath();
  context.restore();
}

function onMouseDown(e) {
  if (e.touches) {
      e = e.touches[0];
  }

  lastEvent = e;
  drawingMode = true;
  document.getElementById('initial_message').style.zIndex = "1"; // Modify z-index
}

function onMouseUp() {
  drawingMode = false;
}

function onMouseMove(e) {
  if (!drawingMode) {
    return;
  }
  if (e.touches) {
    e.preventDefault();
    e = e.touches[0];
  }
  let size = 1;
  
  const deltaX = e.pageX - lastEvent.pageX;
  const deltaY = e.pageY - lastEvent.pageY;
  const distanceToLastMousePosition = Math.sqrt(
    (deltaX ** 2) +
    (deltaY ** 2)
  );

  size = Math.max(minSize, Math.min(maxSize, distanceToLastMousePosition / 3));
  
  if (drawingMode) {
    drawCircle(e.pageX, e.pageY, size, color);
  }
  
  if (lastSize) {
    const deltaSize = size - lastSize;
    
    for (let i = 0; i < distanceToLastMousePosition; i += 1) {
      const shift = (i / distanceToLastMousePosition);
      drawCircle(
        e.pageX - (deltaX * shift),
        e.pageY - (deltaY * shift),
        size - (deltaSize * shift),
        color
      );
    }
  }

  lastEvent = e;
  lastSize = size;
}

canvas.addEventListener('mousedown', onMouseDown);
canvas.addEventListener('touchstart', onMouseDown);

canvas.addEventListener('mousemove', onMouseMove);
canvas.addEventListener('touchmove', onMouseMove);

window.addEventListener('mouseup', onMouseUp);
window.addEventListener('touchend', onMouseUp);