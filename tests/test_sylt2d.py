import contextlib
import glfw
import skia
from OpenGL import GL
import sys
from pysylt_2d import PySyltWorld, PySyltBody

WIDTH, HEIGHT = 640, 480
FPS = 60


@contextlib.contextmanager
def glfw_window():
    if not glfw.init():
        raise RuntimeError("glfw.init() failed")
    glfw.window_hint(glfw.STENCIL_BITS, 8)
    if sys.platform.startswith("darwin"):
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(WIDTH, HEIGHT, "Physics Simulation", None, None)
    if not window:
        glfw.terminate()
        raise RuntimeError("Failed to create GLFW window")

    glfw.make_context_current(window)
    yield window
    glfw.terminate()


@contextlib.contextmanager
def skia_surface(window):
    context = skia.GrDirectContext.MakeGL()
    fb_width, fb_height = glfw.get_framebuffer_size(window)
    backend_render_target = skia.GrBackendRenderTarget(
        fb_width,
        fb_height,
        0,  # sampleCnt
        8,  # stencilBits
        skia.GrGLFramebufferInfo(0, GL.GL_RGBA8),
    )
    surface = skia.Surface.MakeFromBackendRenderTarget(
        context,
        backend_render_target,
        skia.kBottomLeft_GrSurfaceOrigin,
        skia.kRGBA_8888_ColorType,
        skia.ColorSpace.MakeSRGB(),
    )
    assert surface is not None
    yield surface
    context.abandonContext()


# Define colors
WHITE = skia.ColorWHITE
RED = skia.ColorRED
GREEN = skia.ColorGREEN

# Create the world (with gravity)
gravity = (0, 9.8)
world = PySyltWorld(gravity, 10)

# Create bodies
body1 = PySyltBody((50.0, 50.0), 10.0)
body1.set_position(50.0, 0.0)
body3 = PySyltBody((800.0, 40.0), 3.4028235e38)
body3.set_position(30.0, 300.0)

world.add_body(body1)
world.add_body(body3)

with glfw_window() as window:
    with skia_surface(window) as surface:
        while not glfw.window_should_close(window):
            glfw.poll_events()

            # Step the physics simulation
            world.step(1 / FPS)

            # Clear the screen
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)

            # Draw scene
            with surface as canvas:
                canvas.clear(WHITE)

                for body in world.iter_bodies():
                    pos = body.get_position()
                    width, height = body.get_width_height()

                    # Define rectangle (centered on body)
                    rect = skia.Rect.MakeXYWH(
                        pos[0] - width / 2.0, pos[1] - height / 2.0, width, height
                    )

                    # Draw the rectangle
                    paint = skia.Paint()
                    if body.get_id() == 2:
                        paint.setColor(GREEN)
                    else:
                        paint.setColor(RED)
                    canvas.drawRect(rect, paint)

            # Flush and update the display
            surface.flushAndSubmit()
            glfw.swap_buffers(window)
