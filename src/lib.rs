use pyo3::prelude::*;
use std::cell::RefCell;
use std::rc::Rc;

use sylt_2d::body::Body;
use sylt_2d::joint::Joint;
use sylt_2d::math_utils::Vec2;
use sylt_2d::world::World;

#[pyclass]
#[derive(Clone)]
pub struct PySyltBody {
    body: Body,
}

#[pymethods]
impl PySyltBody {
    #[new]
    pub fn new(width_height: (f32, f32), mass: f32) -> Self {
        PySyltBody {
            body: Body::new(
                Vec2 {
                    x: width_height.0,
                    y: width_height.1,
                },
                mass,
            ),
        }
    }

    #[staticmethod]
    pub fn new_polygon(vertices: Vec<(f32, f32)>, mass: f32) -> PyResult<Self> {
        let vec2_vertices: Vec<Vec2> = vertices.into_iter().map(|(x, y)| Vec2 { x, y }).collect();
        let body = Body::new_polygon(vec2_vertices, mass);
        Ok(PySyltBody { body })
    }

    pub fn get_position(&self) -> (f32, f32) {
        (self.body.position.x, self.body.position.y)
    }

    pub fn get_width_height(&self) -> (f32, f32) {
        (self.body.width.x, self.body.width.y)
    }

    pub fn set_position(&mut self, x: f32, y: f32) {
        self.body.position = Vec2 { x, y }
    }

    pub fn get_id(&self) -> usize {
        self.body.id
    }
}

#[pyclass(unsendable)]
pub struct PySyltWorld {
    world: World,
}

#[pymethods]
impl PySyltWorld {
    #[new]
    pub fn new(gravity: (f32, f32), iterations: u32) -> Self {
        PySyltWorld {
            world: World::new(
                Vec2 {
                    x: gravity.0,
                    y: gravity.1,
                },
                iterations,
            ),
        }
    }

    pub fn add_body(&mut self, body: PySyltBody) {
        self.world.add_body(body.body);
    }

    pub fn step(&mut self, dt: f32) -> PyResult<()> {
        self.world
            .step(dt)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    // Expose the bodies iterator to Python
    pub fn iter_bodies(&self) -> PySyltBodyIterator {
        PySyltBodyIterator {
            iter: self.world.bodies.clone().into_iter(),
        }
    }
}

// Custom iterator for bodies in PySyltWorld
#[pyclass(unsendable)]
pub struct PySyltBodyIterator {
    iter: std::vec::IntoIter<Rc<RefCell<Body>>>,
}

#[pymethods]
impl PySyltBodyIterator {
    // The `__iter__` method, required for Python iteration protocol
    fn __iter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf // Return `self` as the iterator
    }

    // The `__next__` method, required for Python iteration protocol
    fn __next__(mut slf: PyRefMut<Self>) -> Option<PySyltBody> {
        slf.iter.next().map(|body_rc| {
            let body = body_rc.borrow().clone(); // Borrow and clone the Body
            PySyltBody { body } // Wrap the cloned Body in a PySyltBody
        })
    }
}

#[pyclass(unsendable)]
pub struct PySyltJoint {
    inner: Joint,
}

#[pymethods]
impl PySyltJoint {
    #[new]
    pub fn new(
        body_1: PySyltBody,
        body_2: PySyltBody,
        anchor: (f32, f32),
        world: &PySyltWorld,
    ) -> Self {
        PySyltJoint {
            inner: Joint::new(
                body_1.body,
                body_2.body,
                Vec2 {
                    x: anchor.0,
                    y: anchor.1,
                },
                &world.world,
            ),
        }
    }
}

#[pymodule]
fn pysylt_2d(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PySyltBody>()?;
    m.add_class::<PySyltWorld>()?;
    m.add_class::<PySyltJoint>()?;
    Ok(())
}
