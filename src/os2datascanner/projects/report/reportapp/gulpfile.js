// Require all the things:
var gulp          = require("gulp");
var plumber       = require("gulp-plumber");
var rename        = require("gulp-rename");
var autoprefixer  = require("gulp-autoprefixer");
var clean         = require("gulp-clean");
var notify        = require("gulp-notify");

// CSS stuff
var sass          = require("gulp-sass");
var minifyCSS     = require("gulp-minify-css");

var paths = {
    sass_src : "static/src/css/**/*.scss",
    css_dest : "static/dist/css/",
    js_src : "static/src/js/**/*",
    js_dest : "static/dist/js/"
};

// Delete unwanted files
gulp.task("clean", function(cb) {
  return gulp.src("**/.DS_Store")
    .pipe(clean())
    .pipe(notify("Clean complete!"));
});

// Compile SASS to CSS
gulp.task("css", function(cb) {
  gulp.src([paths.sass_src])
    .pipe(plumber({
      errorHandler: function(error) {
        console.log(error.message);
        this.emit("end");
      }
    }))
    .pipe(sass())
    .pipe(autoprefixer({
      grid: "autoplace"
    }))
    .pipe(gulp.dest(paths.css_dest))
    .pipe(rename({
      suffix: ".min"
    }))
    .pipe(minifyCSS())
    .pipe(gulp.dest(paths.css_dest))
    .pipe(notify("SASS complete!"));

    cb();
  });

// Watch files
gulp.task("watch", function(cb) {
  gulp.watch(paths.img_src,  ["minifyImages"])
  gulp.watch(paths.sass_src, ["css"])
  gulp.watch(paths.svg_src,  ["svgSprites"])

  cb();
});
