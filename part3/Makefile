all: plot

run:
	sudo python3 runner.py

experiments:
	sudo python3 run_experiments.py --experiments

plot:
	python3 plot_results.py

clean:
	rm -f results.csv p3_plot.png
	rm -rf __pycache__
