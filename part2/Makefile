all: plot

run:
	sudo python3 demo_runner.py

experiments:
	sudo python3 run_experiments.py

plot: experiments
	python3 plot_results.py

clean:
	rm -f results.csv p2_plot.png
	rm -rf __pycache__
