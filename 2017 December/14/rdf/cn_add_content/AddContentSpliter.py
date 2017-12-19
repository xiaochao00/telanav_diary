import re, os, sys

class AddContentSpliter(object):
    """
        class comment
    """

    def __init__(self, gdf_dir, add_content_dir, out_dir):
        self.gdf_dir = gdf_dir
        self.add_content_dir = add_content_dir
        self.out_dir = out_dir

        self.features = {}

        self.feature_set = {}

    def parse_additional_content(self):
        print '*'*80
        for filename in os.listdir(self.add_content_dir):
            if os.path.splitext(filename)[1].upper() != '.TXT':
                continue

            additional_content = os.path.join(self.add_content_dir, filename)
            self.parse_add_content_file(additional_content)

    def content_type(self, additional_content):
        basename = os.path.basename(additional_content)
        return os.path.splitext(basename)[0]

    def parse_add_content_file(self, additional_content):
        print 'Processing add_content_dir data %s' % additional_content
        feature_count = 0

        features = {}
        for line in open(additional_content):
            grp = line.split(';')

            for item in grp:
                key, val = item.split('=')

                if key == 'Feature_ID':
                    feat_id = int(val)
                    if feat_id not in features:
                        features[feat_id] = []

                    feature_count += 1
                    features[feat_id].append(line)

        content_type = self.content_type(additional_content)
        self.feature_set[content_type] = features

        print '\tFeature in %s = %d' %(content_type, feature_count)

    def parse_gdf_file(self, gdf_file):
        print 'Parsing gdf file %s' %(gdf_file)

        basename = os.path.splitext(os.path.basename(gdf_file))[0]

        additional_dir = os.path.join(self.out_dir, basename)
        if not os.path.exists(additional_dir):
            os.makedirs(additional_dir)

        feature_ids = set()

        for line in open(gdf_file):

            if not line.startswith('60'): continue

            assert (line.strip()[-1] == '0')

            num_exp = int(line[15:20])
            idx = 20
            for i in range(num_exp):
                idx += 1                             # FLD_TYPE
                try:
                    fld_len = int(line[idx: idx+5])
                except:
                    print line
                    break
                idx += 5                             # FLD_LEN

                try:
                    feat_id = int(line[idx: idx+fld_len])
                except:
                    print line
                    break

                feature_ids.add(feat_id)

                idx += fld_len                       # FLD_VAL

        for content_type in self.feature_set:
            addition_content = os.path.join(additional_dir, '%s.txt' % content_type)

            ofs = open(addition_content, 'w')

            features = self.feature_set[content_type]

            feature_count = 0
            for feat_id in feature_ids:
                if feat_id in features:
                    for phonetic_line in features[feat_id]:
                        feature_count += 1
                        ofs.write(phonetic_line)
            print '\t%s feature count in %s is %d' %(content_type, gdf_file, feature_count)
            ofs.close()

    def parse_gdf(self):
        assert (os.path.isdir(self.gdf_dir))
        print '*'*80

        for f in os.listdir(self.gdf_dir):
            if os.path.splitext(f)[1].upper() != '.GDF2' and os.path.splitext(f)[1].upper() != '.GDF':
                continue

            gdf_file = os.path.join(self.gdf_dir, f)
            self.parse_gdf_file(gdf_file)

def usage():
    print 'Usage:'
    print '\t%s gdf_dir additional_content_dir split_content_dir\n' %(os.path.basename(sys.argv[0]))

def main():
    if len(sys.argv) != 4:
        usage()
        sys.exit(-1)

    gdf = sys.argv[1]
    content_dir = sys.argv[2]
    split_dir = sys.argv[3]

    spliter = AddContentSpliter(gdf, content_dir, split_dir)

    spliter.parse_additional_content()
    spliter.parse_gdf()

if __name__ == '__main__':
    main()










