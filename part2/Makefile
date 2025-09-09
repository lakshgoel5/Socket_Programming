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
	python3 plot_part2.py

clean:
	rm -f results.csv p2_plot.png
	rm -rf __pycache__
