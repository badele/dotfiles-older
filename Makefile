all:	powerlinefont

powerlinefont:
	rm -rf /tmp/fonts; \
	cd /tmp; \
	git clone https://github.com/powerline/fonts.git; \
	cd fonts; \
	./install.sh

.PHONY: powerlinefont 
