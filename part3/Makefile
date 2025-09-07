all: plot

run:
	sudo python3 runner.py

experiments:
	sudo python3 run_experiments.py --experiments

plot:
	python3 run_experiments.py --plot

clean:
	rm -f results.csv p2_plot.png
	rm -rf __pycache__
