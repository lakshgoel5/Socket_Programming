all: plot

run:
	sudo mn -c
	sudo python3 runner.py

experiments:
	sudo mn -c
	sudo python3 run_experiments.py

plot:
	sudo mn -c
	sudo python3 run_experiments.py
	python3 plot_results.py

clean:
	rm -f results.csv p4_plot.png
	rm -rf __pycache__
