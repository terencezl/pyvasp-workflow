# run_volume
# move yaml and output files to respective directories
for i in `cat INPUT/element.txt`; do mv run_*$i* cc-$i+N/; done
# inspect plots
for i in `cat INPUT/element.txt`; do cp rocksalt-$i+N/run_volume/eos_fit.pdf RESULTS/plots/eos_fit_$i.pdf; done

# run_elastic
for i in `cat INPUT/element.txt`; do mv run_elastic*$i* rocksalt-$i+N/; done

for i in `cat INPUT/element.txt`; do cp rocksalt-$i+N/run_elastic/c11+2c12.pdf RESULTS/plots/c11+2c12_$i.pdf; done
for i in `cat INPUT/element.txt`; do cp rocksalt-$i+N/run_elastic/c11-c12.pdf RESULTS/plots/c11-c12_$i.pdf; done
for i in `cat INPUT/element.txt`; do cp rocksalt-$i+N/run_elastic/c44.pdf RESULTS/plots/c44_$i.pdf; done
