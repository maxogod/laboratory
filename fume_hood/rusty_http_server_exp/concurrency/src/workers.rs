use std::sync::mpsc;
use std::sync::Arc;
use std::sync::Mutex;
use std::thread;

// a closure that takes no arguments and returns nothing
pub type Job = Box<dyn FnOnce() + Send + 'static>;

pub struct Worker {
    id: usize,
    keep_running: Arc<Mutex<bool>>,
    thread: Option<thread::JoinHandle<()>>,
}

impl Worker {
    pub fn new(id: usize, receiver: Arc<Mutex<mpsc::Receiver<Job>>>) -> Worker {
        let keep_running = Arc::new(Mutex::new(true));
        let keep_running_clone = keep_running.clone();

        let thread = thread::spawn(move || {
            while *keep_running_clone.lock().unwrap() {
                match receiver.lock().unwrap().recv() {
                    Ok(job) => {
                        println!("Worker {} got a job; executing.", id);
                        job();
                    }
                    Err(mpsc::RecvError) => {
                        break;
                    }
                }
            }
        });

        return Worker {
            id,
            keep_running,
            thread: Some(thread),
        };
    }

    pub fn stop(&self) {
        println!("Worker {} stopping.", self.id);
        *self.keep_running.lock().unwrap() = false;
    }

    pub fn join(&mut self) {
        println!("Worker {} joining.", self.id);
        self.thread.take().unwrap().join().unwrap();
    }
}
