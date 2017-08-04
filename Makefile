default: test

test:
	nose2 -F -v

clean:
	rm -f `find -name '*~'`
	rm -rf `find -name '__pycache__'`

coffee: 
	@echo 'Starbucks, New York, +1 917-534-1397 - Opens at 6:00 AM'
