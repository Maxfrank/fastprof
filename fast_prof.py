#!/usr/bin/env python
# encoding: utf-8

import sys, time

class FastProf(object):
	def __init__(self, max_levels=None):
		self.max_levels = max_levels

	def fast_trace(self, timedata, max_levels):
		event_types = [
			"call",
			"return"
		]
		get_time = time.time
		timedata["current_fc"] = timedata
		timedata["funcs"] = {}
		timedata["level"] = 0
		timedata["started"] = 0

		def trace_calls(frame, event, arg):
			if event not in event_types:
				return

			if event == "call":
				timedata["started"] = True
				frm_func_name = frame.f_code.co_name

				if timedata["current_fc"] is timedata and frm_func_name == "__exit__": #blesch, ugly hack for now
					return

				if max_levels and timedata["current_fc"]["level"]+1 > max_levels:
					frm_func_name = "unknown"

				if timedata["current_fc"].has_key("name") and frm_func_name == timedata["current_fc"]["name"]:
					timedata["current_fc"]["rec_level"] += 1 #recursive counter
					timedata["current_fc"]["nums"] += 1

				elif timedata["current_fc"]["funcs"].has_key(frm_func_name): #merge existing
					timedata["current_fc"] = timedata["current_fc"]["funcs"][frm_func_name]
					timedata["current_fc"]["t_st"] = get_time()
					timedata["current_fc"]["nums"] += 1

				else:
					new_func = {
						"name": frm_func_name,
						"parent": timedata["current_fc"],
						"funcs": {},
						"level": timedata["current_fc"]["level"] + 1,
						"rec_level": 1,
						"t_st": get_time(),
						"t_ac": 0,
						"nums": 1
					}

					timedata["current_fc"]["funcs"][frm_func_name] = new_func
					timedata["current_fc"] = new_func

			if event == "return":
				if timedata["started"]:
					if timedata["current_fc"]["rec_level"] > 1:
						timedata["current_fc"]["rec_level"] -= 1
					else:
						time_acc = timedata["current_fc"]["t_ac"]
						timedata["current_fc"]["t_ac"] = time_acc + (get_time() - timedata["current_fc"]["t_st"])
						timedata["current_fc"]["t_st"] = 0
							
						
						if timedata["current_fc"].has_key("parent"):
							timedata["current_fc"] = timedata["current_fc"]["parent"]
						else:
							timedata["current_fc"] = timedata

		return trace_calls

	def purdyprint(self, callstats):
		def iterate_data(root, i):
			for func_name, func_data in root.iteritems():
				spacing = " " * (i*2)
				col_num = (i+1 % 7)
				col = "\033[0;3%dm" % col_num
				sys.stdout.write(col+spacing+"\\\n"+spacing+" -> ")
				sys.stdout.write(col+"%s \033[1;3%dm(total=%f, nums=%d) \033[0m\n" % (func_data["name"], col_num, func_data["t_ac"], func_data["nums"]))

				if func_data.has_key("funcs"):
					iterate_data(func_data["funcs"], i+1)
			
		print "\n\033[0;1m<start> (total: %f)\033[0m" % sum([y["t_ac"] for z, y in callstats["funcs"].iteritems()])
		iterate_data(callstats["funcs"], 0)
		print ""

	def __enter__(self):
		self.timedata = {}
		prof = self.fast_trace(self.timedata, self.max_levels)
		sys.setprofile(prof)

	def __exit__(self, type, value, traceback):
		sys.setprofile(None)
		self.purdyprint(self.timedata)
		

if __name__ == "__main__":
	def gork():
		return

	def mork(arg):
		if arg > 2:
			return gork()
		mork(arg+1)

	def derk2():
		mork(0)

	def derk1():
		derk2()
		return

	def derk():
		derk1()



	with FastProf(max_levels=None):
		derk()
		gork()
