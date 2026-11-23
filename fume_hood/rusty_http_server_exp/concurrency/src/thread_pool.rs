use crate::workers;
use std::sync::mpsc;
use std::sync::Arc;
use std::sync::Mutex;

pub struct ThreadPool {
    workers: Vec<workers::Worker>,
    sender: Option<mpsc::Sender<workers::Job>>,
}

impl ThreadPool {
    pub fn new(amount_of_threads: usize) -> ThreadPool {
        let (sender, receiver) = mpsc::channel();
        let receiver = Arc::new(Mutex::new(receiver));

        let mut workers = Vec::with_capacity(amount_of_threads);

        for id in 0..amount_of_threads {
            workers.push(workers::Worker::new(id as usize, Arc::clone(&receiver)));
        }

        return ThreadPool {
            workers,
            sender: Some(sender),
        };
    }

    pub fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        let job: workers::Job = Box::new(f);
        if let Some(sender) = &self.sender {
            sender.send(job).unwrap();
        }
    }
}

impl Drop for ThreadPool {
    fn drop(&mut self) {
        println!("Dropping ThreadPool.");

        for worker in &mut self.workers {
            worker.stop();
        }

        // close sender channel
        self.sender.take();

        for worker in &mut self.workers {
            worker.join();
        }
    }
}
