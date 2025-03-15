import contextlib
import glfw
import skia
from OpenGL import GL
import sys
from pysylt_2d import PySyltWorld, PySyltBody, PySyltJoint

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
BLUE = skia.ColorBLUE

paint = skia.Paint()

# Create the world (with gravity)
gravity = (0, 9.8)
world = PySyltWorld(gravity, 10)

# Create bodies
body1 = PySyltBody((50.0, 50.0), 30.0)
body1.set_position(200.0, 20.0)
body1.set_friction(0.8)

body2 = PySyltBody((35.0, 35.0), 10)
body2.set_position(2.0, 120.0)
body2.set_rotation(0.0)
body2.set_friction(0.2)

body3 = PySyltBody((800.0, 40.0), float("inf"))
body3.set_position(30.0, 300.0)

body4 = PySyltBody((50.0, 50.0), float("inf"))
body4.set_position(355.0, 255.0)

world.add_body(body1)
world.add_body(body2)
world.add_body(body3)
world.add_body(body4)

# Create and add joints
joint1 = PySyltJoint(body2, body3, (110.0, 120.0), world)
world.add_joint(joint1)


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
                    if body.get_id() == 3:
                        paint.setColor(GREEN)
                    elif body.get_id() == 4:
                        paint.setColor(BLUE)
                    else:
                        paint.setColor(RED)
                    canvas.drawRect(rect, paint)

                paint.setColor(BLUE)
                canvas.drawCircle(
                    110,
                    120,
                    1,
                    paint,
                )

            # Flush and update the display
            surface.flushAndSubmit()
            glfw.swap_buffers(window)
