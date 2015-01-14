structures = ['rocksalt', 'cc']

elements = ['Sc_sv', 'Ti_sv', 'V_sv', 'Cr_pv', 'Mn_pv', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
            'Y_sv', 'Zr_sv', 'Nb_sv', 'Mo_pv', 'Tc_pv', 'Ru_pv', 'Rh_pv', 'Pd', 'Ag', 'Cd',
            'Hf_pv', 'Ta_pv', 'W_pv', 'Re', 'Os', 'Ir', 'Pt', 'Au']



data.loc['rocksalt'][0:10].plot(subplots=True, style='o-', figsize=(5, 6))
fig = plt.gcf()
plt.sca(fig.axes[0])
plt.plot(data.loc['rocksalt'][10:20]['C11'], 'o-')
plt.plot(range(1,9), data.loc['rocksalt'][20:28]['C11'], 'o-')
plt.legend(['C11-3d','C11-4d','C11-5d'], loc=0, fontsize=10)
plt.sca(fig.axes[1])
plt.plot(data.loc['rocksalt'][10:20]['C12'], 'o-')
plt.plot(range(1,9), data.loc['rocksalt'][20:28]['C12'], 'o-')
plt.legend(['C12-3d','C12-4d','C12-5d'], loc=0, fontsize=10)
plt.sca(fig.axes[2])
plt.plot(data.loc['rocksalt'][10:20]['C44'], 'o-')
plt.plot(range(1,9), data.loc['rocksalt'][20:28]['C44'], 'o-')
plt.legend(['C44-3d','C44-4d','C44-5d'], loc=0, fontsize=10)
fig.axes[2].xaxis.set_ticklabels(range(3,13), rotation=0)
plt.xlabel('Group Number')
plt.ylim(-10, 200)
plt.tight_layout()
plt.savefig('rocksalt-elastic.pdf')


data.loc['cc'][0:10].plot(subplots=True, style='o-', figsize=(5, 6))
fig = plt.gcf()
plt.sca(fig.axes[0])
plt.plot(data.loc['cc'][10:20]['C11'], 'o-')
plt.plot(range(1,9), data.loc['cc'][20:28]['C11'], 'o-')
plt.legend(['C11-3d','C11-4d','C11-5d'], loc=0, fontsize=10)
plt.sca(fig.axes[1])
plt.plot(data.loc['cc'][10:20]['C12'], 'o-')
plt.plot(range(1,9), data.loc['cc'][20:28]['C12'], 'o-')
plt.legend(['C12-3d','C12-4d','C12-5d'], loc=0, fontsize=10)
plt.sca(fig.axes[2])
plt.plot(data.loc['cc'][10:20]['C44'], 'o-')
plt.plot(range(1,9), data.loc['cc'][20:28]['C44'], 'o-')
plt.legend(['C44-3d','C44-4d','C44-5d'], loc=0, fontsize=10)
fig.axes[2].xaxis.set_ticklabels(range(3,13), rotation=0)
plt.xlabel('Group Number')
plt.ylim(-10, 150)
plt.tight_layout()
plt.savefig('cc-elastic.pdf')